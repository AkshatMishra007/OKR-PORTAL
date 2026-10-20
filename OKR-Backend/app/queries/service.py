"""
Query service.

Responsibilities:
- Handle query business logic.
- Coordinate repository operations.
"""

from uuid import UUID
from datetime import datetime, UTC
from math import ceil
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.users.models import User
from app.queries import repository
from app.queries.models import (
    Query,
    QueryStatus,
    QueryPriority,
)
from app.queries.schemas import (
    QueryCreate,
    QueryListFilters,
    QueryListResponse,
    QueryStatusUpdate,
    QueryResolve,
    QueryDashboardResponse,
    QueryStatusAnalytics,
    QueryPriorityAnalytics,
)
from app.query_activity.models import QueryActivityType
from app.query_activity.service import log_query_activity
from app.organization_members.models import OrganizationMember
from app.common.exceptions import BadRequestException
from app.queries.access import require_query_access
from app.queries.validators import validate_status_transition
from app.rbac.access import get_access_scope


def _resolve_user(db: Session, current_user: User | UUID | None) -> User | None:
    if isinstance(current_user, User):
        return current_user
    if isinstance(current_user, UUID):
        return db.query(User).filter(User.id == current_user, User.is_deleted.is_(False)).first()
    return None


def _generate_ticket_number(
    db: Session,
) -> str:
    """
    Generate the next ticket number.

    Format:
        QRY-000001
        QRY-000002
        ...
    """

    last_query = repository.get_last_query(db)

    if not last_query:
        return "QRY-000001"

    try:
        last_number = int(
            last_query.ticket_number.split("-")[1]
        )
    except (
        IndexError,
        ValueError,
    ):
        last_number = 0

    next_number = last_number + 1

    return f"QRY-{next_number:06d}"


def create_query_service(
    db: Session,
    query_data: QueryCreate,
    current_user_id: UUID,
):
    """
    Create a new support query.
    """

    ticket_number = _generate_ticket_number(db)

    query = Query(
        ticket_number=ticket_number,
        user_id=current_user_id,
        subject=query_data.subject,
        message=query_data.message,
        priority=query_data.priority,
        status=QueryStatus.OPEN,
        created_by=current_user_id,
    )

    query = repository.create_query(
        db,
        query,
    )

    log_query_activity(
        db=db,
        query_id=query.id,
        activity_type=QueryActivityType.CREATED,
        description="Query created.",
        performed_by=current_user_id,
    )

    return query


def get_query_service(
    db: Session,
    query_id: UUID,
    current_user: User,
):
    """
    Get query details by ID with RBAC authorization.
    """

    query = repository.get_query_by_id(
        db,
        query_id,
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found.",
        )

    require_query_access(
        db=db,
        user=current_user,
        query=query,
    )

    return query


def get_query_by_ticket_service(
    db: Session,
    ticket_number: str,
    current_user: User | UUID | None = None,
):
    """
    Get query details by ticket number.
    """

    query = repository.get_query_by_ticket_number(
        db,
        ticket_number,
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found.",
        )

    if current_user:
        user_obj = _resolve_user(db, current_user)
        if user_obj:
            require_query_access(db, user_obj, query, write=False)

    return query


def assign_query_service(
    db: Session,
    query_id: UUID,
    assigned_to: UUID,
    current_user_id: User | UUID,
    current_user: User | None = None,
):
    """
    Assign a query to a user.
    """

    # ------------------------------------
    # Get Query
    # ------------------------------------

    query = repository.get_query_by_id(
        db,
        query_id,
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found.",
        )

    user_obj = current_user or _resolve_user(db, current_user_id)
    if user_obj:
        require_query_access(
            db=db,
            user=user_obj,
            query=query,
            write=True,
        )

    perf_user_id = user_obj.id if user_obj else (current_user_id.id if isinstance(current_user_id, User) else current_user_id)

    # ------------------------------------
    # Get User
    # ------------------------------------

    user = (
        db.query(User)
        .filter(
            User.id == assigned_to,
            User.is_deleted.is_(False),
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not user.is_active:
        raise BadRequestException(
            "Cannot assign query to an inactive user."
        )

    if query.assigned_to == assigned_to:
        raise BadRequestException(
            "Query is already assigned to this user."
        )

    # ------------------------------------
    # Assign Query
    # ------------------------------------

    query.assigned_to = assigned_to

    query.assigned_at = datetime.now(UTC)
    query.updated_by = perf_user_id

    if query.status == QueryStatus.OPEN:
        query.status = QueryStatus.IN_PROGRESS

    updated_query = repository.update_query(
        db,
        query,
    )

    log_query_activity(
        db=db,
        query_id=query.id,
        activity_type=QueryActivityType.ASSIGNED,
        description=f"Query assigned to {user.first_name} {user.last_name}.",
        performed_by=perf_user_id,
    )

    return updated_query


def get_queries_service(
    db: Session,
    filters: QueryListFilters,
):
    """
    Retrieve queries with filtering, sorting and pagination.
    """

    items, total = repository.get_queries(
        db=db,
        page=filters.page,
        page_size=filters.page_size,
        search=filters.search,
        status=filters.status,
        priority=filters.priority,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )
    total_pages = ceil(total / filters.page_size) if total else 0

    return QueryListResponse(
        items=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages,
    )


def update_query_status_service(
    db: Session,
    query_id: UUID,
    query_status: QueryStatusUpdate,
    current_user_id: User | UUID,
    current_user: User | None = None,
):
    """
    Update query status.
    """

    # ------------------------------------
    # Get Query
    # ------------------------------------

    query = repository.get_query_by_id(
        db,
        query_id,
    )

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found.",
        )

    user_obj = current_user or _resolve_user(db, current_user_id)
    if user_obj:
        require_query_access(
            db=db,
            user=user_obj,
            query=query,
            write=True,
        )

    perf_user_id = user_obj.id if user_obj else (current_user_id.id if isinstance(current_user_id, User) else current_user_id)

    # ------------------------------------
    # Validate Status Transition
    # ------------------------------------

    validate_status_transition(
        current_status=query.status,
        new_status=query_status.status,
    )

    # ------------------------------------
    # Update Status
    # ------------------------------------

    query.status = query_status.status

    if query_status.status == QueryStatus.CLOSED:
        if not query.closed_at:
            query.closed_at = datetime.now(UTC)
        if not query.closed_by:
            query.closed_by = perf_user_id
    elif query_status.status == QueryStatus.RESOLVED:
        if not query.resolved_at:
            query.resolved_at = datetime.now(UTC)
        if not query.resolved_by:
            query.resolved_by = perf_user_id

    updated_query = repository.update_query(
        db,
        query,
    )

    log_query_activity(
        db=db,
        query_id=query.id,
        activity_type=QueryActivityType.STATUS_UPDATED,
        description=f"Status changed to {query.status.value}.",
        performed_by=perf_user_id,
    )

    return updated_query


def resolve_query_service(
    db: Session,
    query_id: UUID,
    resolution_data: QueryResolve,
    current_user_id: User | UUID,
    current_user: User | None = None,
):
    """
    Resolve a query.
    """

    # ------------------------------------
    # Get Query
    # ------------------------------------
    query = repository.get_query_by_id(db, query_id)

    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found.",
        )

    user_obj = current_user or _resolve_user(db, current_user_id)
    if user_obj:
        require_query_access(
            db=db,
            user=user_obj,
            query=query,
            write=True,
        )

    perf_user_id = user_obj.id if user_obj else (current_user_id.id if isinstance(current_user_id, User) else current_user_id)

    # ------------------------------------
    # Validate Status Transition
    # ------------------------------------
    validate_status_transition(
        current_status=query.status,
        new_status=QueryStatus.RESOLVED,
    )

    if not resolution_data.resolution_note or not resolution_data.resolution_note.strip():
        raise BadRequestException(
            "Resolution note is required."
        )

    # ------------------------------------
    # Resolve Query
    # ------------------------------------
    query.status = QueryStatus.RESOLVED
    query.resolution_note = resolution_data.resolution_note
    query.resolved_by = perf_user_id
    query.resolved_at = datetime.now(UTC)
    query.updated_by = perf_user_id

    updated_query = repository.update_query(
        db,
        query,
    )

    log_query_activity(
        db=db,
        query_id=query.id,
        activity_type=QueryActivityType.RESOLVED,
        description=f"Query resolved. Resolution Note: {resolution_data.resolution_note}",
        performed_by=perf_user_id,
    )

    return updated_query


def close_query_service(
    db: Session,
    query_id: UUID,
    current_user_id: User | UUID,
    current_user: User | None = None,
):
    """
    Close a query.
    """
    # ------------------------------------
    # Get Query
    # ------------------------------------
    query = repository.get_query_by_id(
        db,
        query_id,
    )
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found.",
        )

    user_obj = current_user or _resolve_user(db, current_user_id)
    if user_obj:
        require_query_access(
            db=db,
            user=user_obj,
            query=query,
            write=True,
        )

    perf_user_id = user_obj.id if user_obj else (current_user_id.id if isinstance(current_user_id, User) else current_user_id)

    # ------------------------------------
    # Validate Status Transition
    # ------------------------------------
    validate_status_transition(
        current_status=query.status,
        new_status=QueryStatus.CLOSED,
    )

    # ------------------------------------
    # Close Query
    # ------------------------------------
    query.status = QueryStatus.CLOSED
    query.closed_by = perf_user_id
    query.closed_at = datetime.now(UTC)

    updated_query = repository.update_query(
        db,
        query,
    )

    log_query_activity(
        db=db,
        query_id=query.id,
        activity_type=QueryActivityType.CLOSED,
        description="Query closed.",
        performed_by=perf_user_id,
    )

    return updated_query

def get_my_queries_service(
    db: Session,
    current_user_id: UUID,
    filters: QueryListFilters,
):
    """
    Retrieve queries raised by or assigned to the current user.    """

    items, total = repository.get_my_queries(
        db=db,
        user_id=current_user_id,
        page=filters.page,
        page_size=filters.page_size,
        search=filters.search,
        status=filters.status,
        priority=filters.priority,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )
    print("total queries for id",current_user_id,items)
    total_pages = (
        ceil(total / filters.page_size)
        if total
        else 0
    )

    return QueryListResponse(
        items=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages,
    )
def get_team_queries_service(
    db: Session,
    current_user_id: UUID,
    filters: QueryListFilters,
):
    """
    Retrieve queries assigned to members
    of the current user's organization.
    """

    # ------------------------------------------------------
    # Find user's organization
    # ------------------------------------------------------

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == current_user_id,
            OrganizationMember.is_deleted.is_(False),
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of any organization.",
        )

    # ------------------------------------------------------
    # Fetch team queries
    # ------------------------------------------------------

    items, total = repository.get_team_queries(
        db=db,
        organization_id=membership.organization_id,
        page=filters.page,
        page_size=filters.page_size,
        search=filters.search,
        status=filters.status,
        priority=filters.priority,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )

    total_pages = (
        ceil(total / filters.page_size)
        if total
        else 0
    )

    return QueryListResponse(
        items=items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=total_pages,
    )
def get_query_dashboard_service(
    db: Session,
):
    """
    Retrieve query dashboard and analytics data.
    """

    stats = repository.get_query_dashboard_stats(db)

    status_counts = stats["status_counts"]
    priority_counts = stats["priority_counts"]

    return QueryDashboardResponse(
        total_queries=stats["total_queries"],

        status_counts=QueryStatusAnalytics(
            OPEN=status_counts.get(QueryStatus.OPEN, 0),
            IN_PROGRESS=status_counts.get(
                QueryStatus.IN_PROGRESS,
                0,
            ),
            RESOLVED=status_counts.get(
                QueryStatus.RESOLVED,
                0,
            ),
            CLOSED=status_counts.get(
                QueryStatus.CLOSED,
                0,
            ),
            REOPENED=status_counts.get(
                QueryStatus.REOPENED,
                0,
            ),
        ),

        priority_counts=QueryPriorityAnalytics(
            LOW=priority_counts.get(
                QueryPriority.LOW,
                0,
            ),
            MEDIUM=priority_counts.get(
                QueryPriority.MEDIUM,
                0,
            ),
            HIGH=priority_counts.get(
                QueryPriority.HIGH,
                0,
            ),
            URGENT=priority_counts.get(
                QueryPriority.URGENT,
                0,
            ),
        ),

        average_resolution_time=stats[
            "average_resolution_time"
        ],

        average_closure_time=stats[
            "average_closure_time"
        ],
    )
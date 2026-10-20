"""
Query repository.

Responsibilities:
- Perform database operations for queries.
- No business logic.
"""

from uuid import UUID
from sqlalchemy import asc, desc, or_, func
from sqlalchemy.orm import Session

from app.queries.models import Query
from app.organization_members.models import OrganizationMember


def create_query(db: Session, query: Query):
    """
    Save a new Query.
    """
    db.add(query)
    db.commit()
    db.refresh(query)

    return query


def get_query_by_id(
    db: Session,
    query_id: UUID
):
    """
    Fetch Query by ID.
    """
    return (
        db.query(Query)
        .filter(
            Query.id == query_id,
            Query.is_deleted.is_(False),
        )
        .first()
    )


def get_query_by_ticket_number(
    db: Session,
    ticket_number: str
):
    """
    Fetch Query by Ticket Number.
    """
    return (
        db.query(Query).filter(
            Query.ticket_number == ticket_number,
            Query.is_deleted.is_(False))
            .first()        
    )


def update_query(
    db: Session,
    query: Query
):
    """
    Persist updated query.
    """
    db.commit()
    db.refresh(query)
    return query


def delete_query(
    db: Session,
    query: Query
):
    """
    Soft Delete
    """
    db.commit()
    db.refresh(query)
    return query


def get_last_query(
    db: Session,
):
    """
    Fetch the most recently created query.
    """

    return (
        db.query(Query)
        .filter(
            Query.is_deleted.is_(False),
        )
        .order_by(
            Query.created_at.desc(),
        )
        .first()
    )


def get_queries(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
    status=None,
    priority=None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc"
):
    """
    Fetch queries with filtering, sorting and pagination.
    """
    query = (
        db.query(Query).filter(
            Query.is_deleted.is_(False),
        )
    )
    # ------------------------------------------------------
    # Search
    # ------------------------------------------------------

    if search:
        query = query.filter(
            or_(
                Query.ticket_number.ilike(f"%{search}%"),
                Query.subject.ilike(f"%{search}%")
            )
        )
    # ------------------------------------------------------
    # Filters
    # ------------------------------------------------------
    if status:
        query = query.filter(
            Query.status == status
        )
    if priority:
        query = query.filter(
            Query.priority == priority
        )
    
    # ------------------------------------------------------
    # Sorting
    # ------------------------------------------------------
    sort_column = getattr(
        Query,
        sort_by,
        Query.submitted_at,
    )
    if sort_order.lower() == "asc":
        query = query.order_by(
            asc(sort_column)
        )
    else:
        query = query.order_by(
            desc(sort_column)
        )
    # ------------------------------------------------
    # Total Count
    # ------------------------------------------------
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    # ------------------------------------------------
    # Pagination
    # ------------------------------------------------
    items = (
        query.offset(
            (page - 1) * page_size
        ).limit(page_size).all()
    )
    return items, total


def get_my_queries(
    db: Session,
    user_id: UUID,
    page: int,
    page_size: int,
    search: str | None = None,
    status=None,
    priority=None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
):
    """
    Fetch queries raised by or assigned to the current user
    with filtering, sorting and pagination.
    """

    query = (

        db.query(Query)
        .filter(
            Query.created_by==user_id,

            Query.is_deleted.is_(False),
        )
    )


    # ------------------------------------------------------
    # Search
    # ------------------------------------------------------

    if search:
        query = query.filter(
            or_(
                Query.ticket_number.ilike(f"%{search}%"),
                Query.subject.ilike(f"%{search}%"),
            )
        )

    # ------------------------------------------------------
    # Filters
    # ------------------------------------------------------

    if status:
        query = query.filter(
            Query.status == status
        )

    if priority:
        query = query.filter(
            Query.priority == priority
        )

    # ------------------------------------------------------
    # Sorting
    # ------------------------------------------------------

    sort_column = getattr(
        Query,
        sort_by,
        Query.submitted_at,
    )

    if sort_order.lower() == "asc":
        query = query.order_by(
            asc(sort_column)
        )
    else:
        query = query.order_by(
            desc(sort_column)
        )

    # ------------------------------------------------------
    # Count
    # ------------------------------------------------------

    total = query.count()

    # ------------------------------------------------------
    # Pagination
    # ------------------------------------------------------

    items = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total


def get_team_queries(
    db: Session,
    organization_id: UUID,
    page: int,
    page_size: int,
    search: str | None = None,
    status=None,
    priority=None,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
):
    """
    Fetch queries assigned to members of an organization
    with filtering, sorting and pagination.
    """

    query = (
        db.query(Query)
        .join(
            OrganizationMember,
            Query.assigned_to == OrganizationMember.user_id,
        )
        .filter(
            OrganizationMember.organization_id == organization_id,
            Query.is_deleted.is_(False),
            OrganizationMember.is_deleted.is_(False),
        )
    )

    # ------------------------------------------------------
    # Search
    # ------------------------------------------------------

    if search:
        query = query.filter(
            or_(
                Query.ticket_number.ilike(f"%{search}%"),
                Query.subject.ilike(f"%{search}%"),
            )
        )

    # ------------------------------------------------------
    # Filters
    # ------------------------------------------------------

    if status:
        query = query.filter(
            Query.status == status
        )

    if priority:
        query = query.filter(
            Query.priority == priority
        )

    # ------------------------------------------------------
    # Sorting
    # ------------------------------------------------------

    sort_column = getattr(
        Query,
        sort_by,
        Query.submitted_at,
    )

    if sort_order.lower() == "asc":
        query = query.order_by(
            asc(sort_column)
        )
    else:
        query = query.order_by(
            desc(sort_column)
        )

    # ------------------------------------------------------
    # Count
    # ------------------------------------------------------

    total = query.count()

    # ------------------------------------------------------
    # Pagination
    # ------------------------------------------------------

    items = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total


def get_query_dashboard_stats(
    db: Session,
):
    """
    Fetch aggregated query dashboard statistics.
    """
    base_query = db.query(Query).filter(
        Query.is_deleted.is_(False)
    )
    # ------------------------------------------------------
    # Total Queries
    # ------------------------------------------------------
    total_queries = base_query.count()
    # ------------------------------------------------------
    # Queries by Status
    # ------------------------------------------------------   
    status_counts = (
        db.query(
            Query.status,
            func.count(Query.id),
        ).filter(
            Query.is_deleted.is_(False),
        )
        .group_by(Query.status)
        .all()
    )
    status_map = {
        status: count
        for status, count in status_counts
    }
    # ------------------------------------------------------
    # Queries by Priority
    # ------------------------------------------------------

    priority_counts = (
        db.query(
            Query.priority,
            func.count(Query.id),
        )
        .filter(
            Query.is_deleted.is_(False),
        )
        .group_by(Query.priority)
        .all()
    )

    priority_map = {
        priority: count
        for priority, count in priority_counts
    }

    # ------------------------------------------------------
    # Average Resolution Time
    # ------------------------------------------------------

    average_resolution_time = (
        db.query(
            func.avg(
                func.extract(
                    "epoch",
                    Query.resolved_at - Query.submitted_at,
                )
            )
        )
        .filter(
            Query.is_deleted.is_(False),
            Query.resolved_at.isnot(None),
        )
        .scalar()
    )

    # ------------------------------------------------------
    # Average Closure Time
    # ------------------------------------------------------

    average_closure_time = (
        db.query(
            func.avg(
                func.extract(
                    "epoch",
                    Query.closed_at - Query.submitted_at,
                )
            )
        )
        .filter(
            Query.is_deleted.is_(False),
            Query.closed_at.isnot(None),
        )
        .scalar()
    )

    return {
        "total_queries": total_queries,

        "status_counts": status_map,

        "priority_counts": priority_map,

        "average_resolution_time": (
            int(average_resolution_time)
            if average_resolution_time is not None
            else None
        ),

        "average_closure_time": (
            int(average_closure_time)
            if average_closure_time is not None
            else None
        ),
    }

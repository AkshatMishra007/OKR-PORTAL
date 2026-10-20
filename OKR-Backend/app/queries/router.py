from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.queries.schemas import (
    QueryAssignment,
    QueryCreate,
    QueryResponse,
    QueryListFilters,
    QueryListResponse,
    QueryStatusUpdate,
    QueryResolve,
    QueryDashboardResponse,
)
from app.queries.service import (
    assign_query_service,
    create_query_service,
    get_query_service,
    get_queries_service,
    update_query_status_service,
    resolve_query_service,
    close_query_service,
    get_my_queries_service,
    get_team_queries_service,
    get_query_dashboard_service,
)
from app.users.models import User
from app.queries.access import (
    require_query_list_access,
    require_team_query_access,
    require_dashboard_access,
)

router = APIRouter(
    prefix="/queries",
    tags=["Queries"]
)

@router.post(
    "/",
    response_model=QueryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_query(
    query_data: QueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new support query.
    """
    return create_query_service(
        db=db,
        query_data=query_data,
        current_user_id=current_user.id,
    )


@router.get(
    "/",
    response_model=QueryListResponse,
)
def get_queries(
    filters: QueryListFilters = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve queries with filtering, sorting and pagination.
    """
    require_query_list_access(
        db=db,
        user=current_user,
    )

    return get_queries_service(
        db=db,
        filters=filters
    )


@router.get(
    "/my",
    response_model=QueryListResponse,
)
def get_my_queries(
    filters: QueryListFilters = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get queries assigned to the current user.
    """

    return get_my_queries_service(
        db=db,
        current_user_id=current_user.id,
        filters=filters,
    )


@router.get(
    "/team",
    response_model=QueryListResponse,
)
def get_team_queries(
    filters: QueryListFilters = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get queries assigned to members of the
    current user's organization.
    """
    require_team_query_access(
        db=db,
        user=current_user,
    )

    return get_team_queries_service(
        db=db,
        current_user_id=current_user.id,
        filters=filters,
    )


@router.get(
    "/dashboard",
    response_model=QueryDashboardResponse,
)
def get_query_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get query dashboard and analytics.
    """
    require_dashboard_access(
        db=db,
        user=current_user,
    )

    return get_query_dashboard_service(db)


@router.get(
    "/{query_id}",
    response_model=QueryResponse
)
def get_query(
    query_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get Query Details
    """
    return get_query_service(
        db=db,
        query_id=query_id,
        current_user=current_user,
    )


@router.patch(
    "/{query_id}/assign",
    response_model=QueryResponse,
)
def assign_query(
    query_id: UUID,
    assignment: QueryAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign a query to a user.
    """

    return assign_query_service(
        db=db,
        query_id=query_id,
        assigned_to=assignment.assigned_to,
        current_user_id=current_user.id,
        current_user=current_user,
    )


@router.patch(
    "/{query_id}/status",
    response_model=QueryResponse,
)
def update_query_status(
    query_id: UUID,
    query_status: QueryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update query status.
    """

    return update_query_status_service(
        db=db,
        query_id=query_id,
        query_status=query_status,
        current_user_id=current_user.id,
        current_user=current_user,
    )


@router.patch(
    "/{query_id}/resolve",
    response_model=QueryResponse,
)
def resolve_query(
    query_id: UUID,
    resolution_data: QueryResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resolve a query.
    """
    return resolve_query_service(
        db=db,
        query_id=query_id,
        resolution_data=resolution_data,
        current_user_id=current_user.id,
        current_user=current_user,
    )


@router.patch(
    "/{query_id}/close",
    response_model=QueryResponse,
)
def close_query(
    query_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    close a query
    """
    return close_query_service(
        db=db,
        query_id=query_id,
        current_user_id=current_user.id,
        current_user=current_user,
    )
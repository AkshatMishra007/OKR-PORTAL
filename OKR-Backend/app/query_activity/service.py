from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.queries.repository import get_query_by_id
from app.query_activity import repository
from app.query_activity.models import (
    QueryActivity,
    QueryActivityType,
)
from app.query_activity.schemas import QueryActivityListResponse

def log_query_activity(
    db: Session,
    query_id: UUID,
    activity_type: QueryActivityType,
    description: str,
    performed_by: UUID,
):
    """
    Log an activity for a query.
    """

    activity = QueryActivity(
        query_id=query_id,
        activity_type=activity_type,
        description=description,
        performed_by=performed_by,
    )

    return repository.create_activity(
        db=db,
        activity=activity,
    )

def get_query_activity_history(
    db: Session,
    query_id: UUID,
    page: int = 1,
    size: int = 20,
    activity_type: QueryActivityType | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "asc",
):
    """
    Retrieve activity history for a query with pagination, sorting, and filtering.
    """
    query = get_query_by_id(
        db=db,
        query_id=query_id,
    )
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query not found.",
        )

    activities, total = repository.get_query_activities(
        db=db,
        query_id=query_id,
        page=page,
        size=size,
        activity_type=activity_type,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return QueryActivityListResponse(
        activities=activities,
        total=total,
        page=page,
        size=size,
    )
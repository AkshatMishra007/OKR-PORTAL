from uuid import UUID
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.query_activity.schemas import QueryActivityListResponse
from app.query_activity.service import get_query_activity_history
from app.users.models import User

router =APIRouter(
    prefix="/queries",
    tags=["Query Activity"],
)
from fastapi import APIRouter, Depends, Query
from app.query_activity.models import QueryActivityType

@router.get(
    "/{query_id}/activities",
    response_model=QueryActivityListResponse,
)
def get_query_activites(
    query_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    activity_type: QueryActivityType | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="asc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve activity history for a query.
    """
    return get_query_activity_history(
        db=db,
        query_id=query_id,
        page=page,
        size=size,
        activity_type=activity_type,
        sort_by=sort_by,
        sort_order=sort_order,
    )
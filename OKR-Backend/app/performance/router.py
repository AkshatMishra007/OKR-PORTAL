from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.performance import service
from app.performance.schemas import PerformanceResponse
from app.users.models import User


router = APIRouter(
    prefix="/performance",
    tags=["Performance"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/",
    response_model=PerformanceResponse,
)
def get_performance(
    batch_id: UUID | None = Query(
        default=None,
        description="Filter performance metrics by batch.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_performance(
        db=db,
        current_user_id=current_user.id,
        batch_id=batch_id,
    )
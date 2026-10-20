from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.users.models import User
from app.weekly_update.schemas import (
    WeeklyUpdateCreate,
    WeeklyUpdateListResponse,
    WeeklyUpdateResponse,
    WeeklyUpdateUpdate,
)
from app.weekly_update.service import WeeklyUpdateService

router = APIRouter(
    tags=["Weekly Updates"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/okrs/{okr_id}/weekly-updates",
    response_model=WeeklyUpdateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_weekly_update(
    okr_id: UUID,
    update_data: WeeklyUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new weekly update for an OKR.
    """
    service = WeeklyUpdateService(db)
    return service.create_weekly_update(
        okr_id=okr_id,
        update_data=update_data,
        current_user=current_user,
    )


@router.get(
    "/okrs/{okr_id}/weekly-updates",
    response_model=WeeklyUpdateListResponse,
)
def get_weekly_updates_for_okr(
    okr_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    min_progress: float | None = Query(default=None),
    max_progress: float | None = Query(default=None),
    sort_by: str | None = Query(default="week_number"),
    sort_order: str | None = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List paginated weekly updates for a specific OKR.
    """
    service = WeeklyUpdateService(db)
    return service.get_weekly_updates_for_okr(
        okr_id=okr_id,
        page=page,
        size=size,
        search=search,
        min_progress=min_progress,
        max_progress=max_progress,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )


@router.get(
    "/weekly-updates/{update_id}",
    response_model=WeeklyUpdateResponse,
)
def get_weekly_update(
    update_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch a single weekly update by ID.
    """
    service = WeeklyUpdateService(db)
    return service.get_weekly_update(
        update_id=update_id,
        current_user=current_user,
    )


@router.put(
    "/weekly-updates/{update_id}",
    response_model=WeeklyUpdateResponse,
)
def update_weekly_update(
    update_id: UUID,
    update_data: WeeklyUpdateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing weekly update.
    """
    service = WeeklyUpdateService(db)
    return service.update_weekly_update(
        update_id=update_id,
        update_data=update_data,
        current_user=current_user,
    )


@router.delete(
    "/weekly-updates/{update_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_weekly_update(
    update_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a weekly update.
    """
    service = WeeklyUpdateService(db)
    service.delete_weekly_update(
        update_id=update_id,
        current_user=current_user,
    )
    return None

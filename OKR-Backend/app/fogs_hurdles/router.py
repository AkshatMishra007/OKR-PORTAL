"""
FOGS & Hurdles router.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.fogs_hurdles.schemas import (
    FogsHurdleCreate,
    FogsHurdleListResponse,
    FogsHurdleResponse,
    FogsHurdleUpdate,
)
from app.fogs_hurdles.service import FogsHurdleService
from app.users.models import User

router = APIRouter(
    tags=["FOGS & Hurdles"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/okrs/{okr_id}/fogs-hurdles",
    response_model=FogsHurdleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fogs_hurdle(
    okr_id: UUID,
    hurdle_data: FogsHurdleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FogsHurdleService(db)
    return service.create_fogs_hurdle(
        okr_id=okr_id,
        hurdle_data=hurdle_data,
        current_user=current_user,
    )


@router.get(
    "/okrs/{okr_id}/fogs-hurdles",
    response_model=FogsHurdleListResponse,
)
def get_fogs_hurdles_for_okr(
    okr_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FogsHurdleService(db)
    return service.get_fogs_hurdles_for_okr(
        okr_id=okr_id,
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )


@router.get(
    "/fogs-hurdles/{fogs_hurdle_id}",
    response_model=FogsHurdleResponse,
)
def get_fogs_hurdle(
    fogs_hurdle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FogsHurdleService(db)
    return service.get_fogs_hurdle(
        fogs_hurdle_id=fogs_hurdle_id,
        current_user=current_user,
    )


@router.put(
    "/fogs-hurdles/{fogs_hurdle_id}",
    response_model=FogsHurdleResponse,
)
def update_fogs_hurdle(
    fogs_hurdle_id: UUID,
    update_data: FogsHurdleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FogsHurdleService(db)
    return service.update_fogs_hurdle(
        fogs_hurdle_id=fogs_hurdle_id,
        update_data=update_data,
        current_user=current_user,
    )


@router.delete(
    "/fogs-hurdles/{fogs_hurdle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_fogs_hurdle(
    fogs_hurdle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FogsHurdleService(db)
    service.delete_fogs_hurdle(
        fogs_hurdle_id=fogs_hurdle_id,
        current_user=current_user,
    )
    return None

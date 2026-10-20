from typing import List
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

from app.my_okr import service
from app.my_okr.schemas import (
    OKRCreate,
    OKRResponse,
    OKRUpdate,
    OKRListResponse,
)

router = APIRouter(
    prefix="/okrs",
    tags=["OKRs"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=OKRResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_okr(
    okr_data: OKRCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return service.create_okr(
        db=db,
        okr_data=okr_data,
        current_user=current_user,
    )


@router.get(
    "/",
    response_model=OKRListResponse,
)
def get_okrs(
    organization_id: UUID | None = Query(default=None),
    batch_id: UUID | None = Query(default=None),
    assigned_to: UUID | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    tracker_enabled: bool | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    page: int = Query(
        default=1,
        ge=1,
    ),
    size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return service.get_okrs(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        batch_id=batch_id,
        assigned_to=assigned_to,
        user_id=user_id,
        search=search,
        status=status,
        tracker_enabled=tracker_enabled,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/user/{user_id}",
    response_model=OKRListResponse,
)
def get_okrs_by_user(
    user_id: UUID,
    batch_id: UUID | None = Query(default=None),
    organization_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    tracker_enabled: bool | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    page: int = Query(
        default=1,
        ge=1,
    ),
    size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return service.get_okrs_by_user(
        db=db,
        user_id=user_id,
        current_user=current_user,
        organization_id=organization_id,
        batch_id=batch_id,
        search=search,
        status=status,
        tracker_enabled=tracker_enabled,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/{okr_id}",
    response_model=OKRResponse,
)
def get_okr(
    okr_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return service.get_okr(
        db=db,
        okr_id=okr_id,
        current_user=current_user,
    )


@router.put(
    "/{okr_id}",
    response_model=OKRResponse,
)
def update_okr(
    okr_id: UUID,
    okr_data: OKRUpdate,

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return service.update_okr(
        db=db,
        okr_id=okr_id,
        okr_data=okr_data,
        current_user=current_user,
    )


@router.delete(
    "/{okr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_okr(
    okr_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    service.delete_okr(
        db=db,
        okr_id=okr_id,
        current_user=current_user,
    )

    return None
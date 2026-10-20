from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.batch_members.schemas import (
    BatchMemberCreate,
    BatchMemberListResponse,
    BatchMemberResponse,
    BatchMemberUpdate,
)
from app.batch_members.service import (
    create_batch_member_service,
    delete_batch_member_service,
    get_batch_member_service,
    list_batch_members_service,
    update_batch_member_service,
)
from app.core.database import get_db
from app.users.models import User

router = APIRouter(
    prefix="/batch-members",
    tags=["Batch Members"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=BatchMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_batch_member(
    member: BatchMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchMemberResponse:
    return create_batch_member_service(
        db=db,
        member_data=member,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=BatchMemberListResponse,
)
def list_batch_members(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    batch_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return list_batch_members_service(
        db=db,
        page=page,
        size=size,
        batch_id=batch_id,
        user_id=user_id,
        role_id=role_id,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )


@router.get(
    "/{member_id}",
    response_model=BatchMemberResponse,
)
def get_batch_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchMemberResponse:
    return get_batch_member_service(
        db=db,
        member_id=member_id,
        current_user=current_user,
    )


@router.put(
    "/{member_id}",
    response_model=BatchMemberResponse,
)
def update_batch_member(
    member_id: UUID,
    member: BatchMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchMemberResponse:
    return update_batch_member_service(
        db=db,
        member_id=member_id,
        member_data=member,
        current_user=current_user,
    )


@router.delete(
    "/{member_id}",
    response_model=BatchMemberResponse,
    status_code=status.HTTP_200_OK,
)
def delete_batch_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchMemberResponse:
    return delete_batch_member_service(
        db=db,
        member_id=member_id,
        current_user=current_user,
    )

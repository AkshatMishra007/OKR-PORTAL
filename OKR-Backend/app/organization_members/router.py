from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.organization_members.schemas import (
    OrganizationMemberCreate,
    OrganizationMemberListResponse,
    OrganizationMemberResponse,
    OrganizationMemberUpdate,
)
from app.organization_members.service import (
    create_member_service,
    delete_member_service,
    get_member_service,
    list_members_service,
    update_member_service,
)

from app.users.models import User

router = APIRouter(
    prefix="/organization-members",
    tags=["Organization Members"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_member(
    member: OrganizationMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationMemberResponse:
    return create_member_service(
        db=db,
        member_data=member,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=OrganizationMemberListResponse,
)
def list_members(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    organization_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return list_members_service(
        db=db,
        page=page,
        size=size,
        organization_id=organization_id,
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
    response_model=OrganizationMemberResponse,
)
def get_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationMemberResponse:
    return get_member_service(
        db=db,
        member_id=member_id,
        current_user=current_user,
    )


@router.put(
    "/{member_id}",
    response_model=OrganizationMemberResponse,
)
def update_member(
    member_id: UUID,
    member: OrganizationMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationMemberResponse:
    return update_member_service(
        db=db,
        member_id=member_id,
        member_data=member,
        current_user=current_user,
    )


@router.delete(
    "/{member_id}",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_200_OK,
)
def delete_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrganizationMemberResponse:
    return delete_member_service(
        db=db,
        member_id=member_id,
        current_user=current_user,
    )

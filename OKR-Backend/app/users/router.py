from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.rbac.dependencies import require_permission
from app.users.models import User
from app.users.schemas import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.users.service import (
    create_user_service,
    delete_user,
    get_user_by_id,
    get_users,
    get_users_by_organization_service,
    update_user,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],
)



@router.post(
    "/",
    response_model=UserResponse,
    status_code=201,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.create")
    ),
):

    user = create_user_service(
        db=db,
        user_data=user_data,
        current_user=current_user,
    )

    return user


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_profile(
    current_user: User = Depends(get_current_user),
):

    return current_user


@router.get(
    "/organization/{organization_id}",
    response_model=UserListResponse,
)
def get_users_by_organization_api(
    organization_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=1000),
    search: str | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.view")),
):

    users, total = get_users_by_organization_service(
        db=db,
        organization_id=organization_id,
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        is_active=is_active,
        current_user=current_user,
    )

    return {
        "data": users,
        "page": page,
        "size": size,
        "total": total,
    }


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return get_user_by_id(
        db,
        user_id,
        current_user=current_user,
    )


@router.get(
    "/",
    response_model=UserListResponse,
)
def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    is_active: bool | None = Query(default=None),
    designation: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    organization_id: UUID | None = Query(default=None),
    org_id_header: UUID | None = Header(default=None, alias="X-Organization-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.view")
    ),
):
    target_org_id = organization_id or org_id_header

    users, total = get_users(
        db=db,
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        is_active=is_active,
        designation=designation,
        created_after=created_after,
        created_before=created_before,
        current_user=current_user,
        organization_id=target_org_id,
    )

    return {
        "data": users,
        "page": page,
        "size": size,
        "total": total,
    }


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user_api(
    user_id: UUID,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.update")
    ),
):

    return update_user(
        db,
        user_id,
        data,
        current_user=current_user,
    )


@router.delete(
    "/{user_id}",
)
def delete_user_api(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("user.delete")),
):

    delete_user(
        db,
        user_id,
        current_user=current_user,
    )

    return {"success": True, "message": "User deleted successfully."}

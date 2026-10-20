from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.auth.dependencies import get_current_user

from app.rbac.schemas import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
)

from app.rbac.service import (
    create_role_service,
    get_role_service,
    list_roles_service,
    update_role_service,
    delete_role_service,
)


router = APIRouter(
    prefix="/roles",
    tags=["RBAC"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
):
    return create_role_service(
        db,
        role_data,
    )


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
):
    return get_role_service(
        db,
        role_id,
    )


from fastapi import Query

@router.get(
    "/",
    response_model=RoleListResponse,
)
def list_roles(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None),
    is_system_role: bool | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    sort_by: str | None = Query(default="name"),
    sort_order: str | None = Query(default="asc"),
    db: Session = Depends(get_db),
):
    if is_system_role is None and is_active is None and (sort_by is None or sort_by == "name") and (sort_order is None or sort_order == "asc"):
        roles, total = list_roles_service(
            db,
            page,
            size,
            search,
        )
    else:
        roles, total = list_roles_service(
            db=db,
            page=page,
            size=size,
            search=search,
            is_system_role=is_system_role,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    return {
        "data": roles,
        "page": page,
        "size": size,
        "total": total,
    }


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
)
def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
):
    return update_role_service(
        db,
        role_id,
        role_data,
    )


@router.delete(
    "/{role_id}",
)
def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db),
):
    delete_role_service(
        db,
        role_id,
    )

    return {
        "success": True,
        "message": "Role deleted successfully.",
    }
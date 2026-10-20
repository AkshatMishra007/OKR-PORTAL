from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    RoleAlreadyExistsException,
    RoleNotFoundException,
)

from app.rbac import repository
from app.rbac.repository import (
    create_role,
    get_role_by_id,
    get_role_by_name,
    list_roles,
    update_role,
    delete_role,
)

from app.rbac.schemas import (
    RoleCreate,
    RoleUpdate,
)


def create_role_service(
    db: Session,
    role_data: RoleCreate,
):

    existing = get_role_by_name(
        db,
        role_data.name,
    )

    if existing:
        raise RoleAlreadyExistsException(
            "Role name already exists."
        )

    return create_role(
        db,
        role_data,
    )


def get_role_service(
    db: Session,
    role_id: UUID,
):

    role = get_role_by_id(
        db,
        role_id,
    )

    if not role:
        raise RoleNotFoundException(
            "Role not found."
        )

    return role


def list_roles_service(
    db: Session,
    page: int = 1,
    size: int = 10,
    search: str | None = None,
    is_system_role: bool | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
):

    if is_system_role is None and is_active is None and sort_by is None and sort_order is None:
        return list_roles(
            db,
            page,
            size,
            search,
        )

    get_kwargs = {
        "page": page,
        "size": size,
        "search": search,
    }
    if is_system_role is not None:
        get_kwargs["is_system_role"] = is_system_role
    if is_active is not None:
        get_kwargs["is_active"] = is_active
    if sort_by is not None:
        get_kwargs["sort_by"] = sort_by
    if sort_order is not None:
        get_kwargs["sort_order"] = sort_order

    return list_roles(
        db,
        **get_kwargs,
    )


def update_role_service(
    db: Session,
    role_id: UUID,
    role_data: RoleUpdate,
):

    role = get_role_by_id(
        db,
        role_id,
    )

    if not role:
        raise RoleNotFoundException(
            "Role not found."
        )

    if role_data.name:

        existing = get_role_by_name(
            db,
            role_data.name,
        )

        if existing and existing.id != role.id:
            raise RoleAlreadyExistsException(
                "Role name already exists."
            )

    return update_role(
        db,
        role,
        role_data,
    )


def delete_role_service(
    db: Session,
    role_id: UUID,
):

    role = get_role_by_id(
        db,
        role_id,
    )

    if not role:
        raise RoleNotFoundException(
            "Role not found."
        )

    delete_role(
        db,
        role,
    )

    return True
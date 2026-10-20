from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.rbac.models import Role
from app.rbac.schemas import (
    RoleCreate,
    RoleUpdate,
)


def create_role(
    db: Session,
    role_data: RoleCreate,
) -> Role:

    role = Role(
        name=role_data.name,
        description=role_data.description,
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    return role



def get_role_by_id(
    db: Session,
    role_id: UUID,
) -> Role | None:

    return (
        db.query(Role)
        .filter(
            Role.id == role_id,
            Role.is_deleted.is_(False),
        )
        .first()
    )



def get_role_by_name(
    db: Session,
    name: str,
) -> Role | None:

    return (
        db.query(Role)
        .filter(
            Role.name == name,
            Role.is_deleted.is_(False),
        )
        .first()
    )



from app.common.query import validate_and_apply_sorting, paginate_query

ALLOWED_ROLE_SORT_FIELDS = {
    "name": Role.name,
    "created_at": Role.created_at,
    "updated_at": Role.updated_at,
}


def list_roles(
    db: Session,
    page: int = 1,
    size: int = 10,
    search: str | None = None,
    is_system_role: bool | None = None,
    is_active: bool | None = None,
    sort_by: str | None = "name",
    sort_order: str | None = "asc",
):

    query = db.query(Role).filter(
        Role.is_deleted.is_(False)
    )

    if search:
        query = query.filter(
            or_(
                Role.name.ilike(f"%{search}%"),
                Role.description.ilike(f"%{search}%"),
            )
        )

    if is_system_role is not None and hasattr(Role, "is_system_role"):
        query = query.filter(Role.is_system_role == is_system_role)

    if is_active is not None and hasattr(Role, "is_active"):
        query = query.filter(Role.is_active == is_active)

    query = validate_and_apply_sorting(
        query=query,
        model=Role,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_ROLE_SORT_FIELDS,
        default_sort_column=Role.name,
    )

    items, meta = paginate_query(query=query, page=page, size=size)
    return list(items), meta["total"]



def update_role(
    db: Session,
    role: Role,
    role_data: RoleUpdate,
):

    update_data = role_data.model_dump(
        exclude_unset=True
    )


    for key, value in update_data.items():
        setattr(
            role,
            key,
            value,
        )


    db.commit()
    db.refresh(role)

    return role



def delete_role(
    db: Session,
    role: Role,
):

    role.is_active = False
    role.is_deleted = True

    db.commit()
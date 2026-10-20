"""
User repository layer.

Responsibilities:
- Direct database access for User model.
- Queries, creations, updates, soft deletions of users.

This layer does not:
- Handle HTTP requests or FastAPI routers.
- Contain business rule validations or password hashing.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.common.query import paginate_query, validate_and_apply_sorting
from app.organization_members.models import OrganizationMember
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate

ALLOWED_USER_SORT_FIELDS = {
    "username": User.username,
    "email": User.email,
    "first_name": User.first_name,
    "last_name": User.last_name,
    "created_at": User.created_at,
}


def get_user_joined_options():
    from app.batches.models import BatchMember
    return (
        joinedload(User.organization_members).joinedload(OrganizationMember.organization),
        joinedload(User.organization_members).joinedload(OrganizationMember.role),
        joinedload(User.batch_members).joinedload(BatchMember.batch),
    )


def create_user(
    db: Session,
    user_data: UserCreate,
    password_hash: str,
) -> User:
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        designation=user_data.designation,
        description=user_data.description,
    )
    db.add(user)
    db.flush()
    return user


def get_user_by_id(
    db: Session,
    user_id: UUID,
) -> User | None:
    return (
        db.query(User)
        .options(*get_user_joined_options())
        .filter(
            User.id == user_id,
            User.is_deleted.is_(False),
        )
        .first()
    )


def get_user_by_username(
    db: Session,
    username: str,
) -> User | None:
    return (
        db.query(User)
        .options(*get_user_joined_options())
        .filter(
            User.username == username,
            User.is_deleted.is_(False),
        )
        .first()
    )


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return (
        db.query(User)
        .options(*get_user_joined_options())
        .filter(
            User.email == email,
            User.is_deleted.is_(False),
        )
        .first()
    )


def get_users(
    db: Session,
    page: int = 1,
    size: int = 10,
    search: str | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
    is_active: bool | None = None,
    designation: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    organization_ids: list[UUID] | None = None,
    batch_ids: list[UUID] | None = None,
) -> tuple[list[User], int]:
    """
    Retrieve a paginated list of non-deleted users, with optional search, filters, sorting,
    and multi-tenant scoping (organization_ids, batch_ids), eagerly loading relations.
    """
    if organization_ids is not None and len(organization_ids) == 0:
        return [], 0
    if batch_ids is not None and len(batch_ids) == 0:
        return [], 0

    query = (
        db.query(User)
        .options(*get_user_joined_options())
        .filter(User.is_deleted.is_(False))
    )

    if organization_ids is not None or batch_ids is not None:
        if organization_ids is not None:
            query = query.filter(
                db.query(OrganizationMember.id)
                .filter(
                    OrganizationMember.user_id == User.id,
                    OrganizationMember.is_deleted.is_(False),
                    OrganizationMember.is_active.is_(True),
                    OrganizationMember.organization_id.in_(organization_ids),
                )
                .exists()
            )
        if batch_ids is not None:
            from app.batches.models import BatchMember
            query = query.filter(
                db.query(BatchMember.id)
                .filter(
                    BatchMember.user_id == User.id,
                    BatchMember.is_deleted.is_(False),
                    BatchMember.is_active.is_(True),
                    BatchMember.batch_id.in_(batch_ids),
                )
                .exists()
            )

    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if designation:
        query = query.filter(User.designation.ilike(f"%{designation}%"))

    if created_after:
        query = query.filter(User.created_at >= created_after)

    if created_before:
        query = query.filter(User.created_at <= created_before)

    query = validate_and_apply_sorting(
        query=query,
        model=User,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_USER_SORT_FIELDS,
        default_sort_column=User.created_at,
    )

    items, meta = paginate_query(query=query, page=page, size=size)
    return list(items), meta["total"]


def get_users_by_organization(
    db: Session,
    organization_id: UUID,
    page: int = 1,
    size: int = 10,
    search: str | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
    is_active: bool | None = None,
) -> tuple[list[User], int]:
    """
    Retrieve a paginated list of users belonging to a specific organization via organization_members,
    along with their assigned role in that organization and eagerly loaded relations.
    """
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    base_query = (
        db.query(User, Role)
        .options(*get_user_joined_options())
        .join(OrganizationMember, OrganizationMember.user_id == User.id)
        .outerjoin(Role, Role.id == OrganizationMember.role_id)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.is_deleted.is_(False),
            User.is_deleted.is_(False),
        )
    )

    if search:
        base_query = base_query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
            )
        )

    if is_active is not None:
        base_query = base_query.filter(User.is_active == is_active)

    base_query = validate_and_apply_sorting(
        query=base_query,
        model=User,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_USER_SORT_FIELDS,
        default_sort_column=User.created_at,
    )

    items, meta = paginate_query(query=base_query, page=page, size=size)

    users = []
    for user, role in items:
        user.role = role
        users.append(user)

    return users, meta["total"]



def update_user(
    db: Session,
    user: User,
    user_data: UserUpdate,
) -> User:

    print("Updating user:", user.id)

    update_data = user_data.model_dump(
        exclude_unset=True
    )

    print("Update data:", update_data)

    # =================================================
    # Extract OrganizationMember fields
    # =================================================

    organization_id = update_data.pop(
        "organization_id",
        None
    )

    role_id = update_data.pop(
        "role_id",
        None
    )

    # =================================================
    # Extract Password
    # =================================================

    password = update_data.pop(
        "password",
        None
    )

    # =================================================
    # Update User fields
    # =================================================

    for field, value in update_data.items():
        setattr(user, field, value)

    # =================================================
    # Update Password
    # =================================================

    if password is not None:
        user.password_hash = password

    # =================================================
    # Update OrganizationMember
    # =================================================

    if (
        organization_id is not None
        or role_id is not None
    ):

        membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == user.id,
                OrganizationMember.is_deleted == False,
            )
            .first()
        )

        if membership is None:

            # Create membership if it doesn't exist
            if (
                organization_id is None
                or role_id is None
            ):
                raise ValueError(
                    "Organization ID and Role ID are required."
                )

            membership = OrganizationMember(
                user_id=user.id,
                organization_id=organization_id,
                role_id=role_id,
            )

            db.add(membership)

        else:

            # Update organization if provided
            if organization_id is not None:
                membership.organization_id = organization_id

            # Update role if provided
            if role_id is not None:
                membership.role_id = role_id

    # =================================================
    # Save
    # =================================================

    db.commit()

    db.refresh(user)

    return user

def delete_user(
    db: Session,
    user: User,
) -> User:
    """
    Soft-delete a User instance by setting is_deleted=True.
    """
    user.is_deleted = True
    db.commit()
    db.refresh(user)

    return user

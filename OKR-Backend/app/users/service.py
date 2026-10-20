"""
User service layer.

Responsibilities:
- User business logic.
- Coordinate user database operations via repository layer.

This layer does not:
- Handle HTTP requests.
- Return API responses.
- Contain router logic.
"""

from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.auth.password import hash_password
from app.common.exceptions import (
    ForbiddenException,
    OrganizationNotFoundException,
    RoleNotFoundException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.organization_members.models import OrganizationMember
from app.organization_members.repository import create_organization_member
from app.organizations.repository import get_organization_by_id
from app.rbac.dependencies import is_super_admin, normalize_role_code
from app.rbac.policies import RoleCode
from app.rbac.repository import get_role_by_id
from app.users import repository
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate


def _validate_user_tenant_access(
    db: Session,
    current_user: User | None,
    target_user_id: UUID | None = None,
    organization_id: UUID | None = None,
    action: str = "view",
) -> None:
    if not current_user:
        return

    if is_super_admin(current_user, db=db):
        return

    if target_user_id and target_user_id == current_user.id and action in ("view", "update"):
        return

    caller_memberships = (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.role))
        .filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .all()
    )

    if not caller_memberships:
        return

    caller_roles = {
        normalize_role_code(m.role.name) for m in caller_memberships if m.role
    }

    if RoleCode.ORG_ADMIN.value not in caller_roles:
        raise ForbiddenException("You do not have permission to manage users.")

    caller_org_ids = {m.organization_id for m in caller_memberships if m.organization_id}

    if organization_id and organization_id not in caller_org_ids:
        raise ForbiddenException("Access denied to users in another organization.")

    if target_user_id:
        target_memberships = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == target_user_id,
                OrganizationMember.is_deleted.is_(False),
                OrganizationMember.is_active.is_(True),
            )
            .all()
        )
        target_org_ids = {m.organization_id for m in target_memberships if m.organization_id}
        if target_org_ids and not (target_org_ids & caller_org_ids):
            raise ForbiddenException("Access denied to users outside your organization.")


def create_user_service(
    db: Session,
    user_data: UserCreate,
    current_user: User | None = None,
) -> User:
    """
    Create a new user and corresponding organization member in one transaction.
    """
    # ------------------------------------
    # Check duplicate username
    # ------------------------------------

    existing_username = repository.get_user_by_username(
        db=db,
        username=user_data.username,
    )

    if existing_username:
        raise UserAlreadyExistsException("Username already exists.")

    # ------------------------------------
    # Check duplicate email
    # ------------------------------------

    existing_email = repository.get_user_by_email(
        db=db,
        email=user_data.email,

    )

    if existing_email:
        raise UserAlreadyExistsException("Email already exists.")

    # ------------------------------------
    # Validate Organization and Role existence
    # ------------------------------------

    organization = get_organization_by_id(
        db=db,
        organization_id=user_data.organization_id,
    )

    if not organization:
        raise OrganizationNotFoundException("Organization not found.")

    role = get_role_by_id(
        db=db,
        role_id=user_data.role_id,
    )

    if not role:
        raise RoleNotFoundException("Role not found.")

    if normalize_role_code(role.name) == RoleCode.SUPER_ADMIN.value and not is_super_admin(current_user, db=db):
        raise ForbiddenException("Only super admins can assign the super admin role.")

    _validate_user_tenant_access(
        db=db,
        current_user=current_user,
        organization_id=user_data.organization_id,
        action="create",
    )

    # ------------------------------------
    # Hash Password
    # ------------------------------------

    hashed_password = hash_password(user_data.password)

    # ------------------------------------
    # ------------------------------------
    # Create User and OrganizationMember in single transaction
    # ------------------------------------

    try:
        user = repository.create_user(
            db=db,
            user_data=user_data,
            password_hash=hashed_password,
        )

        create_organization_member(
            db=db,
            organization_id=user_data.organization_id,
            user_id=user.id,
            role_id=user_data.role_id,
            created_by=getattr(current_user, "id", None) if current_user else None,
        )

        batch_id = getattr(user_data, "batch_id", None)
        if batch_id:
            from app.batches.models import BatchMember
            batch_member = BatchMember(
                batch_id=batch_id,
                user_id=user.id,
                role_id=user_data.role_id,
                created_by=getattr(current_user, "id", None) if current_user else None,
            )
            db.add(batch_member)

        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise

# =====================================================
# Get User By ID
# =====================================================


def get_user_by_id(
    db: Session,
    user_id: UUID,
    current_user: User | None = None,
) -> User:

    _validate_user_tenant_access(
        db=db,
        current_user=current_user,
        target_user_id=user_id,
        action="view",
    )

    user = repository.get_user_by_id(
        db=db,
        user_id=user_id,
    )

    if not user:
        raise UserNotFoundException("User not found.")

    return user


# =====================================================
# Get All Users
# =====================================================


from datetime import datetime

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
    current_user: User | None = None,
    organization_id: UUID | None = None,
):
    organization_ids = None
    batch_ids = None

    if current_user and not is_super_admin(current_user, db=db):
        caller_memberships = (
            db.query(OrganizationMember)
            .options(joinedload(OrganizationMember.role))
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_deleted.is_(False),
                OrganizationMember.is_active.is_(True),
            )
            .all()
        )
        if not caller_memberships:
            raise ForbiddenException("User is not a member of any organization.")

        allowed_org_ids = {m.organization_id for m in caller_memberships if m.organization_id}

        if organization_id and organization_id not in allowed_org_ids:
            raise ForbiddenException("Access denied to users in another organization.")

        caller_roles = {
            normalize_role_code(m.role.name) for m in caller_memberships if m.role
        }

        if RoleCode.ORG_ADMIN.value in caller_roles:
            if organization_id:
                target_org = organization_id
            elif len(allowed_org_ids) == 1:
                target_org = next(iter(allowed_org_ids))
            else:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Multiple organization memberships found. Please pass 'X-Organization-ID' header.",
                )
            organization_ids = [target_org]
        elif RoleCode.BATCH_ADMIN.value in caller_roles:
            from app.batches.models import BatchMember
            caller_batch_memberships = (
                db.query(BatchMember)
                .filter(
                    BatchMember.user_id == current_user.id,
                    BatchMember.is_deleted.is_(False),
                    BatchMember.is_active.is_(True),
                )
                .all()
            )
            caller_batch_ids = [bm.batch_id for bm in caller_batch_memberships if bm.batch_id is not None]
            batch_ids = caller_batch_ids
        else:
            raise ForbiddenException("You do not have permission to view users.")
    elif organization_id:
        organization_ids = [organization_id]

    return repository.get_users(
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
        organization_ids=organization_ids,
        batch_ids=batch_ids,
    )


# =====================================================
# Get Users By Organization
# =====================================================


def get_users_by_organization_service(
    db: Session,
    organization_id: UUID,
    page: int = 1,
    size: int = 10,
    search: str | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
    is_active: bool | None = None,
    current_user: User | None = None,
):
    _validate_user_tenant_access(
        db=db,
        current_user=current_user,
        organization_id=organization_id,
        action="view",
    )

    return repository.get_users_by_organization(
        db=db,
        organization_id=organization_id,
        page=page,
        size=size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        is_active=is_active,
    )


def get_users_by_organization(
    db: Session,
    organization_id: UUID,
    page: int = 1,
    size: int = 10,
    search: str | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
    is_active: bool | None = None,
    current_user: User | None = None,
):
    return get_users_by_organization_service(
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


# =====================================================
# Update User
# =====================================================


def update_user(
    db: Session,
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User | None = None,
):

    _validate_user_tenant_access(
        db=db,
        current_user=current_user,
        target_user_id=user_id,
        action="update",
    )

    user = get_user_by_id(
        db,
        user_id,
        current_user=current_user,
    )

    # =================================================
    # Hash password if provided
    # =================================================

    if user_data.password is not None:

        print("Password is given")

        user_data = user_data.model_copy(
            update={
                "password": hash_password(
                    user_data.password
                )
            }
        )

    return repository.update_user(
        db=db,
        user=user,
        user_data=user_data,
    )


# =====================================================
# Delete User
# =====================================================


def delete_user(
    db: Session,
    user_id: UUID,
    current_user: User | None = None,
):

    _validate_user_tenant_access(
        db=db,
        current_user=current_user,
        target_user_id=user_id,
        action="delete",
    )

    user = get_user_by_id(
        db,
        user_id,
        current_user=current_user,
    )

    repository.delete_user(
        db=db,
        user=user,
    )

    return True

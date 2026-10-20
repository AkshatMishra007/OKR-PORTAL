from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.common.exceptions import (
    AppException,
    ForbiddenException,
    OrganizationMemberAlreadyExistsException,
    OrganizationMemberNotFoundException,
    OrganizationNotFoundException,
    RoleNotFoundException,
    UserNotFoundException,
)
from app.organization_members import repository
from app.organization_members.models import OrganizationMember
from app.organization_members.schemas import (
    OrganizationMemberCreate,
    OrganizationMemberUpdate,
)
from app.organizations import repository as organization_repository
from app.rbac import repository as rbac_repository
from app.rbac.dependencies import is_super_admin, normalize_role_code
from app.rbac.policies import RoleCode
from app.users import service as user_service
from app.users.models import User

BATCH_REQUIRED_ROLES = {
    "batch_admin",
    "employee",
    "student",
}

NO_BATCH_ROLES = {
    "super_admin",
    "org_admin",
    "admin",
}


def _validate_role_batch_rule(
    role,
    batch_id: UUID | None = None,
):
    return


def _validate_member_tenant_access(
    db: Session,
    current_user: User | None,
    organization_id: UUID,
    batch_id: UUID | None = None,
    action: str = "view",
) -> None:
    if not current_user:
        return

    if is_super_admin(current_user, db=db):
        return

    caller_all_memberships = (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.role))
        .filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .all()
    )

    if not caller_all_memberships:
        return

    caller_memberships = [m for m in caller_all_memberships if m.organization_id == organization_id]

    if not caller_memberships:
        raise ForbiddenException("You are not an active member of this organization.")

    caller_roles = {
        normalize_role_code(m.role.name) for m in caller_memberships if m.role
    }

    if RoleCode.ORG_ADMIN.value in caller_roles:
        return

    if RoleCode.BATCH_ADMIN.value in caller_roles:
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
        caller_batch_ids = {m.batch_id for m in caller_batch_memberships}
        if batch_id is not None and batch_id not in caller_batch_ids:
            raise ForbiddenException("Batch Admin cannot manage members outside assigned batch.")
        return

    raise ForbiddenException("Employees are not authorized to perform member management operations.")


def create_member_service(
    db: Session,
    member_data: OrganizationMemberCreate,
    current_user: User | None = None,
    current_user_id=None,
):
    """
    Create a new organization member.
    """
    if current_user_id is None and current_user is not None:
        current_user_id = getattr(current_user, "id", None)

    _validate_member_tenant_access(
        db=db,
        current_user=current_user,
        organization_id=member_data.organization_id,
        action="create",
    )

    organization = organization_repository.get_organization_by_id(
        db,
        member_data.organization_id,
    )

    if not organization:
        raise OrganizationNotFoundException(
            "Organization not found"
        )

    # -----------------------------------------
    # Validate User
    # -----------------------------------------

    user = user_service.get_user_by_id(
        db,
        member_data.user_id,
    )

    if not user:
        raise UserNotFoundException(
            "User not found"
        )

    # -----------------------------------------
    # Validate Role
    # -----------------------------------------

    role = rbac_repository.get_role_by_id(
        db,
        member_data.role_id,
    )

    if not role:
        raise RoleNotFoundException(
            "Role not found"
        )

    # -----------------------------------------
    # Validate Role - Batch Business Rule
    # -----------------------------------------

    # -----------------------------------------
    # Duplicate Membership Check
    # -----------------------------------------

    existing_member = repository.get_member_by_user_and_organization(
        db,
        member_data.organization_id,
        member_data.user_id,
    )
    if existing_member:
        raise OrganizationMemberAlreadyExistsException(
            "User is already an organization member."
        )

    # -----------------------------------------
    # Create Member
    # -----------------------------------------

    member = OrganizationMember(
        organization_id=member_data.organization_id,
        user_id=member_data.user_id,
        role_id=member_data.role_id,
        created_by=current_user_id,
    )

    return repository.create_member(
        db,
        member,
    )


def get_member_service(
    db: Session,
    member_id: UUID,
    current_user: User | None = None,
):
    """
    Get organization member details.
    """

    member = repository.get_member_by_id(
        db,
        member_id,
    )

    if not member:
        raise OrganizationMemberNotFoundException(
            "Organization member not found."
        )

    _validate_member_tenant_access(
        db=db,
        current_user=current_user,
        organization_id=member.organization_id,
        action="view",
    )

    return member


def list_members_service(
    db: Session,
    page: int = 1,
    size: int = 20,
    organization_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
    current_user: User | None = None,
):
    """
    List organization members.
    """
    if current_user and not is_super_admin(current_user, db=db):
        caller_m = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_deleted.is_(False),
                OrganizationMember.is_active.is_(True),
            )
            .all()
        )
        if not caller_m:
            raise ForbiddenException("User is not a member of any organization.")
        allowed_org_ids = {m.organization_id for m in caller_m}
        if organization_id is not None and organization_id not in allowed_org_ids:
            raise ForbiddenException("Access denied to members in another organization.")
        if organization_id is None and len(allowed_org_ids) == 1:
            organization_id = list(allowed_org_ids)[0]

    skip = (page - 1) * size

    get_kwargs = {
        "skip": skip,
        "limit": size,
        "organization_id": organization_id,
        "user_id": user_id,
        "role_id": role_id,
    }
    count_kwargs = {
        "organization_id": organization_id,
        "user_id": user_id,
        "role_id": role_id,
    }

    if search is not None:
        get_kwargs["search"] = search
        count_kwargs["search"] = search
    if is_active is not None:
        get_kwargs["is_active"] = is_active
        count_kwargs["is_active"] = is_active
    if sort_by is not None:
        get_kwargs["sort_by"] = sort_by
    if sort_order is not None:
        get_kwargs["sort_order"] = sort_order

    members = repository.get_members(
        db,
        **get_kwargs,
    )

    total = repository.count_members(
        db,
        **count_kwargs,
    )

    total_pages = (total + size - 1) // size if total > 0 else 1

    return {
        "data": members,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def update_member_service(
    db: Session,
    member_id: UUID,
    member_data: OrganizationMemberUpdate,
    current_user: User | None = None,
    current_user_id=None,
):
    """
    Update organization member.
    """
    if current_user_id is None and current_user is not None:
        current_user_id = getattr(current_user, "id", None)

    member = repository.get_member_by_id(
        db,
        member_id,
    )

    if not member:
        raise OrganizationMemberNotFoundException(
            "Organization member not found."
        )

    _validate_member_tenant_access(
        db=db,
        current_user=current_user,
        organization_id=member.organization_id,
        action="update",
    )

    if member_data.role_id is not None:
        role = rbac_repository.get_role_by_id(
            db,
            member_data.role_id,
        )

        if not role:
            raise RoleNotFoundException(
                "Role not found"
            )

    update_data = member_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(member, field, value)

    member.updated_by = current_user_id

    return repository.update_member(
        db,
        member,
    )


def delete_member_service(
    db: Session,
    member_id: UUID,
    current_user: User | None = None,
    current_user_id=None,
):
    """
    Soft delete organization member.
    """
    if current_user_id is None and current_user is not None:
        current_user_id = getattr(current_user, "id", None)

    member = repository.get_member_by_id(
        db,
        member_id,
    )

    if not member:
        raise OrganizationMemberNotFoundException(
            "Organization member not found."
        )

    _validate_member_tenant_access(
        db=db,
        current_user=current_user,
        organization_id=member.organization_id,
        action="delete",
    )

    from datetime import UTC, datetime
    member.is_deleted = True
    member.is_active = False
    member.deleted_at = datetime.now(UTC)
    member.updated_by = current_user_id

    return repository.delete_member(
        db,
        member,
    )
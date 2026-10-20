from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.batches import repository as batch_repository
from app.batch_members import repository as batch_member_repository
from app.batch_members.schemas import BatchMemberCreate, BatchMemberUpdate
from app.common.exceptions import (
    AppException,
    BatchMemberNotFoundException,
    BatchNotFoundException,
    ForbiddenException,
    RoleNotFoundException,
    UserNotFoundException,
)
from app.organization_members import repository as organization_member_repository
from app.organization_members.models import OrganizationMember
from app.rbac import repository as rbac_repository
from app.rbac.dependencies import is_super_admin, normalize_role_code
from app.rbac.policies import RoleCode
from app.users import service as user_service
from app.users.models import User


def _get_employee_role(db: Session):
    role = (
        rbac_repository.get_role_by_name(db, "Employee")
        or rbac_repository.get_role_by_name(db, "employee")
        or rbac_repository.get_role_by_name(db, "EMPLOYEE")
    )
    if not role:
        raise RoleNotFoundException("Employee role not found.")
    return role


def _get_batch_admin_role(db: Session):
    role = (
        rbac_repository.get_role_by_name(db, "Batch Admin")
        or rbac_repository.get_role_by_name(db, "batch_admin")
        or rbac_repository.get_role_by_name(db, "BATCH_ADMIN")
    )
    if not role:
        raise RoleNotFoundException("Batch Admin role not found.")
    return role


def _validate_batch_member_access(
    db: Session,
    current_user: User | None,
    batch_id: UUID,
    action: str = "view",
) -> None:
    """
    Validate tenant access for batch member operations:
    - Super Admin: full access
    - Org Admin: access to batches in their organization (via OrganizationMember)
    - Batch Admin: access only to batches they belong to (via BatchMember)
    - Employee: not authorized
    """
    if not current_user:
        return

    if is_super_admin(current_user, db=db):
        return

    batch = batch_repository.get_batch_by_id(db=db, batch_id=batch_id)
    if not batch:
        raise BatchNotFoundException("Batch not found.")

    caller_org_memberships = (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.role))
        .filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.organization_id == batch.organization_id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .all()
    )

    if not caller_org_memberships:
        raise ForbiddenException("You are not an active member of this organization.")

    caller_roles = {
        normalize_role_code(m.role.name) for m in caller_org_memberships if m.role
    }

    if RoleCode.ORG_ADMIN.value in caller_roles:
        return

    if RoleCode.BATCH_ADMIN.value in caller_roles:
        from app.batches.models import BatchMember
        assigned = (
            db.query(BatchMember)
            .filter(
                BatchMember.batch_id == batch.id,
                BatchMember.user_id == current_user.id,
                BatchMember.is_deleted.is_(False),
                BatchMember.is_active.is_(True),
            )
            .first()
        )
        if not assigned:
            raise ForbiddenException("Batch Admin cannot manage members outside assigned batch.")
        return

    raise ForbiddenException("Employees are not authorized to perform batch member operations.")


def create_batch_member_service(
    db: Session,
    member_data: BatchMemberCreate,
    current_user: User | None = None,
):
    """
    Create or reactivate a batch member:
    1. Validate tenant access
    2. Validate batch exists
    3. Validate user exists
    4. Validate user is an active member of the batch's organization via OrganizationMember
    5. Validate role exists
    6. If Employee: verify not active in another batch
    7. If Batch Admin: multiple batches allowed
    8. Check for existing BatchMember: reuse if same role, reject if role change
    9. Never modify OrganizationMember
    """
    current_user_id = current_user.id if current_user else None

    batch = batch_repository.get_batch_by_id(db=db, batch_id=member_data.batch_id)
    if not batch:
        raise BatchNotFoundException("Batch not found.")

    _validate_batch_member_access(
        db=db,
        current_user=current_user,
        batch_id=batch.id,
        action="create",
    )

    user = user_service.get_user_by_id(db, member_data.user_id, current_user=current_user)
    if not user:
        raise UserNotFoundException("User not found.")

    # Validate organization membership via OrganizationMember
    org_member = organization_member_repository.get_member_by_user_and_organization(
        db=db,
        organization_id=batch.organization_id,
        user_id=member_data.user_id,
    )
    if not org_member or not org_member.is_active or org_member.is_deleted:
        raise AppException("User is not an active member of this organization.")

    role = rbac_repository.get_role_by_id(db, member_data.role_id)
    if not role:
        raise RoleNotFoundException("Role not found.")

    role_code = normalize_role_code(role.name)

    # If Employee: enforce single active batch rule
    if role_code == RoleCode.EMPLOYEE.value:
        existing_emp = batch_member_repository.get_employee_membership_in_other_batch(
            db=db,
            organization_id=batch.organization_id,
            user_id=member_data.user_id,
            employee_role_id=role.id,
            current_batch_id=batch.id,
        )
        if existing_emp:
            raise AppException("Employee is already assigned to another batch.")

    # Create or reuse batch member
    member = batch_member_repository.create_batch_member(
        db=db,
        batch_id=member_data.batch_id,
        user_id=member_data.user_id,
        role_id=member_data.role_id,
        created_by=current_user_id,
    )
    db.commit()
    db.refresh(member)
    return member


def get_batch_member_service(
    db: Session,
    member_id: UUID,
    current_user: User | None = None,
):
    """
    Get batch member details by ID.
    """
    member = batch_member_repository.get_batch_member_by_id(db, member_id)
    if not member:
        raise BatchMemberNotFoundException("Batch member not found.")

    _validate_batch_member_access(
        db=db,
        current_user=current_user,
        batch_id=member.batch_id,
        action="view",
    )
    return member


def list_batch_members_service(
    db: Session,
    page: int = 1,
    size: int = 20,
    batch_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
    current_user: User | None = None,
) -> dict:
    """
    List batch members with pagination and filters.
    """
    if batch_id:
        _validate_batch_member_access(
            db=db,
            current_user=current_user,
            batch_id=batch_id,
            action="view",
        )

    skip = (page - 1) * size

    members = batch_member_repository.get_batch_members(
        db=db,
        skip=skip,
        limit=size,
        batch_id=batch_id,
        user_id=user_id,
        role_id=role_id,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    total = batch_member_repository.count_batch_members(
        db=db,
        batch_id=batch_id,
        user_id=user_id,
        role_id=role_id,
        search=search,
        is_active=is_active,
    )

    return {
        "data": members,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
        },
    }


def update_batch_member_service(
    db: Session,
    member_id: UUID,
    member_data: BatchMemberUpdate,
    current_user: User | None = None,
):
    """
    Update a batch member without changing roles automatically.
    """
    current_user_id = current_user.id if current_user else None

    member = batch_member_repository.get_batch_member_by_id(db, member_id)
    if not member:
        raise BatchMemberNotFoundException("Batch member not found.")

    _validate_batch_member_access(
        db=db,
        current_user=current_user,
        batch_id=member.batch_id,
        action="update",
    )

    if member_data.role_id is not None and member_data.role_id != member.role_id:
        raise AppException("Role change for existing batch member is not supported.")

    if member_data.is_active is not None:
        member.is_active = member_data.is_active

    member.updated_by = current_user_id
    member.updated_at = datetime.now(UTC)

    return batch_member_repository.update_batch_member(db, member)


def delete_batch_member_service(
    db: Session,
    member_id: UUID,
    current_user: User | None = None,
):
    """
    Soft delete a batch member without modifying OrganizationMember.
    """
    current_user_id = current_user.id if current_user else None

    member = batch_member_repository.get_batch_member_by_id(db, member_id)
    if not member:
        raise BatchMemberNotFoundException("Batch member not found.")

    _validate_batch_member_access(
        db=db,
        current_user=current_user,
        batch_id=member.batch_id,
        action="delete",
    )

    return batch_member_repository.soft_delete_batch_member(
        db=db,
        member=member,
        updated_by=current_user_id,
    )

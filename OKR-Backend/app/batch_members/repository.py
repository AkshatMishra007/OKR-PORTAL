from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.batches.models import Batch, BatchMember
from app.common.exceptions import AppException
from app.common.query import validate_and_apply_sorting
from app.users.models import User

ALLOWED_BATCH_MEMBER_SORT_FIELDS = {
    "created_at",
    "updated_at",
}


def get_batch_member(
    db: Session,
    batch_id: UUID,
    user_id: UUID,
) -> BatchMember | None:
    """
    Get active/non-deleted batch member by batch_id and user_id.
    """
    return (
        db.query(BatchMember)
        .options(
            joinedload(BatchMember.user),
            joinedload(BatchMember.role),
            joinedload(BatchMember.batch),
        )
        .filter(
            BatchMember.batch_id == batch_id,
            BatchMember.user_id == user_id,
            BatchMember.is_deleted.is_(False),
        )
        .first()
    )


def get_batch_member_by_id(
    db: Session,
    member_id: UUID,
) -> BatchMember | None:
    """
    Get batch member by ID.
    """
    return (
        db.query(BatchMember)
        .options(
            joinedload(BatchMember.user),
            joinedload(BatchMember.role),
            joinedload(BatchMember.batch),
        )
        .filter(
            BatchMember.id == member_id,
            BatchMember.is_deleted.is_(False),
        )
        .first()
    )


def get_batch_members(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    batch_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> list[BatchMember]:
    """
    Get batch members with optional filters, search, sorting, and eagerly loaded relationships.
    """
    query = (
        db.query(BatchMember)
        .options(
            joinedload(BatchMember.user),
            joinedload(BatchMember.role),
            joinedload(BatchMember.batch),
        )
        .filter(
            BatchMember.is_deleted.is_(False),
        )
    )

    if batch_id:
        query = query.filter(BatchMember.batch_id == batch_id)

    if user_id:
        query = query.filter(BatchMember.user_id == user_id)

    if role_id:
        query = query.filter(BatchMember.role_id == role_id)

    if is_active is not None:
        query = query.filter(BatchMember.is_active == is_active)

    if search:
        query = query.join(User, BatchMember.user_id == User.id).filter(
            (User.first_name.ilike(f"%{search}%"))
            | (User.last_name.ilike(f"%{search}%"))
            | (User.email.ilike(f"%{search}%"))
            | (User.username.ilike(f"%{search}%"))
        )

    if sort_by is not None:
        query = validate_and_apply_sorting(
            query=query,
            model=BatchMember,
            sort_by=sort_by,
            sort_order=sort_order,
            allowed_sort_fields=ALLOWED_BATCH_MEMBER_SORT_FIELDS,
            default_sort_column=BatchMember.created_at,
        )
    else:
        query = query.order_by(BatchMember.created_at.desc())

    return query.offset(skip).limit(limit).all()


def count_batch_members(
    db: Session,
    batch_id: UUID | None = None,
    user_id: UUID | None = None,
    role_id: UUID | None = None,
    search: str | None = None,
    is_active: bool | None = None,
) -> int:
    """
    Count batch members matching filters.
    """
    query = db.query(BatchMember).filter(BatchMember.is_deleted.is_(False))

    if batch_id:
        query = query.filter(BatchMember.batch_id == batch_id)

    if user_id:
        query = query.filter(BatchMember.user_id == user_id)

    if role_id:
        query = query.filter(BatchMember.role_id == role_id)

    if is_active is not None:
        query = query.filter(BatchMember.is_active == is_active)

    if search:
        query = query.join(User, BatchMember.user_id == User.id).filter(
            (User.first_name.ilike(f"%{search}%"))
            | (User.last_name.ilike(f"%{search}%"))
            | (User.email.ilike(f"%{search}%"))
            | (User.username.ilike(f"%{search}%"))
        )

    return query.count()


def get_user_active_batch_memberships(
    db: Session,
    user_id: UUID,
) -> list[BatchMember]:
    """
    Get all active batch memberships for a given user.
    """
    return (
        db.query(BatchMember)
        .options(
            joinedload(BatchMember.batch),
            joinedload(BatchMember.role),
        )
        .filter(
            BatchMember.user_id == user_id,
            BatchMember.is_deleted.is_(False),
            BatchMember.is_active.is_(True),
        )
        .all()
    )


def get_employee_membership_in_other_batch(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    employee_role_id: UUID | None = None,
    current_batch_id: UUID | None = None,
) -> BatchMember | None:
    """
    Check if user is already an active Employee in another batch within the organization.
    """
    query = (
        select(BatchMember)
        .join(Batch, BatchMember.batch_id == Batch.id)
        .where(
            Batch.organization_id == organization_id,
            Batch.is_deleted.is_(False),
            BatchMember.user_id == user_id,
            BatchMember.is_deleted.is_(False),
            BatchMember.is_active.is_(True),
        )
    )
    if employee_role_id is not None:
        query = query.where(BatchMember.role_id == employee_role_id)
    if current_batch_id is not None:
        query = query.where(BatchMember.batch_id != current_batch_id)

    return db.execute(query).scalars().first()


def create_batch_member(
    db: Session,
    batch_id: UUID,
    user_id: UUID,
    role_id: UUID,
    created_by: UUID | None = None,
) -> BatchMember:
    """
    Create or reuse an existing batch membership record.
    Prevents silent role changes.
    """
    existing = (
        db.query(BatchMember)
        .filter(
            BatchMember.batch_id == batch_id,
            BatchMember.user_id == user_id,
        )
        .first()
    )
    if existing:
        if existing.role_id != role_id:
            raise AppException("Role change for existing batch member is not supported.")
        existing.is_active = True
        existing.is_deleted = False
        existing.deleted_at = None
        existing.updated_by = created_by
        existing.updated_at = datetime.now(UTC)
        db.flush()
        return existing

    member = BatchMember(
        batch_id=batch_id,
        user_id=user_id,
        role_id=role_id,
        created_by=created_by,
    )
    db.add(member)
    db.flush()
    return member


def update_batch_member(
    db: Session,
    member: BatchMember,
) -> BatchMember:
    """
    Save updates to a batch member.
    """
    member.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(member)
    return member


def soft_delete_batch_member(
    db: Session,
    member: BatchMember,
    updated_by: UUID | None = None,
) -> BatchMember:
    """
    Soft delete a batch member without touching OrganizationMember.
    """
    member.is_deleted = True
    member.is_active = False
    member.deleted_at = datetime.now(UTC)
    member.updated_by = updated_by
    member.updated_at = datetime.now(UTC)
    db.commit()
    return member

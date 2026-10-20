from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import cast, func, select, String
from sqlalchemy.orm import Session, joinedload

from app.batches.models import Batch, BatchMember, Quarter
from app.batches.schemas import BatchCreate, BatchUpdate


def create_batch(
    db: Session,
    batch_data: BatchCreate,
    created_by: UUID | None = None,
) -> Batch:
    """
    Create a new Batch entity in the session and flush to obtain batch.id.
    """
    batch = Batch(
        organization_id=batch_data.organization_id,
        name=batch_data.name,
        year=batch_data.year,
        quarter=batch_data.quarter,
        start_date=batch_data.start_date,
        end_date=batch_data.end_date,
        meeting_day=batch_data.meeting_day,
        created_by=created_by,
    )

    db.add(batch)
    db.flush()

    return batch




def get_batch_by_id(
    db: Session,
    batch_id: UUID,
) -> Batch | None:

    query = (
        select(Batch)
        .where(
            Batch.id == batch_id,
            Batch.is_deleted.is_(False),
        )
    )

    return db.execute(query).scalar_one_or_none()


from app.common.query import validate_and_apply_sorting

ALLOWED_BATCH_SORT_FIELDS = {
    "name": Batch.name,
    "year": Batch.year,
    "quarter": Batch.quarter,
    "start_date": Batch.start_date,
    "end_date": Batch.end_date,
    "status": Batch.status,
    "created_at": Batch.created_at,
}


def get_batches(
    db: Session,
    organization_id: UUID | None = None,
    organization_ids: list[UUID] | None = None,
    batch_ids: list[UUID] | None = None,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    quarter: Quarter | str | None = None,
    status: str | None = None,
    year: int | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
):

    base_query = select(Batch).where(
        Batch.is_deleted.is_(False)
    )

    if organization_id:
        base_query = base_query.where(
            Batch.organization_id == organization_id
        )
    elif organization_ids is not None:
        base_query = base_query.where(
            Batch.organization_id.in_(organization_ids)
        )

    if batch_ids is not None:
        base_query = base_query.where(
            Batch.id.in_(batch_ids)
        )

    if search:
        base_query = base_query.where(
            (Batch.name.ilike(f"%{search}%"))
            | (cast(Batch.year, String).ilike(f"%{search}%"))
        )

    if quarter:
        base_query = base_query.where(Batch.quarter == quarter)

    if status:
        base_query = base_query.where(Batch.status == status)

    if year:
        base_query = base_query.where(Batch.year == year)

    count_query = select(
        func.count()
    ).select_from(
        base_query.subquery()
    )

    total = db.execute(
        count_query
    ).scalar()

    base_query = validate_and_apply_sorting(
        query=base_query,
        model=Batch,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_BATCH_SORT_FIELDS,
        default_sort_column=Batch.created_at,
    )

    batches = (
        base_query
        .offset(
            (page - 1) * size
        )
        .limit(size)
    )

    result = db.execute(
        batches
    ).scalars().all()

    return result, total


def update_batch(
    db: Session,
    batch: Batch,
    batch_data: BatchUpdate,
    updated_by: UUID | None = None,
    commit: bool = True,
) -> Batch:

    update_data = batch_data.model_dump(
        exclude_unset=True,
        exclude={"batch_users", "batch_admins"},
    )

    for field, value in update_data.items():
        setattr(
            batch,
            field,
            value,
        )

    batch.updated_by = updated_by
    batch.updated_at = datetime.now(UTC)

    if commit:
        db.commit()
        db.refresh(batch)
    else:
        db.flush()

    return batch


def soft_delete_batch(
    db: Session,
    batch: Batch,
    deleted_by: UUID | None = None,
) -> Batch:

    batch.is_deleted = True
    batch.is_active = False
    batch.deleted_at = datetime.now(UTC)
    batch.updated_by = deleted_by

    db.commit()
    db.refresh(batch)

    return batch




def get_batch_by_name_year_and_quarter(
    db: Session,
    organization_id: UUID,
    name: str,
    year: int,
    quarter: Quarter,
) -> Batch | None:
    """
    Returns a batch with the same organization, name, year and quarter.
    Used to prevent duplicate batches.
    """

    query = (
        select(Batch)
        .where(
            Batch.organization_id == organization_id,
            Batch.name == name,
            Batch.year == year,
            Batch.quarter == quarter,
            Batch.is_deleted.is_(False),
        )
    )

    return db.execute(query).scalar_one_or_none()
 
 
def get_batch_member(
    db: Session,
    batch_id: UUID,
    user_id: UUID,
    include_deleted: bool = False,
) -> BatchMember | None:
    query = (
        select(BatchMember)
        .options(
            joinedload(BatchMember.user),
            joinedload(BatchMember.role),
            joinedload(BatchMember.batch),
        )
        .where(
            BatchMember.batch_id == batch_id,
            BatchMember.user_id == user_id,
        )
    )
    if not include_deleted:
        query = query.where(
            BatchMember.is_deleted.is_(False),
            BatchMember.is_active.is_(True),
        )

    return db.execute(query).scalars().first()


def get_batch_members(
    db: Session,
    batch_id: UUID,
    role_id: UUID | None = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 10000,
) -> list[BatchMember]:
    query = (
        select(BatchMember)
        .options(
            joinedload(BatchMember.user),
            joinedload(BatchMember.role),
            joinedload(BatchMember.batch),
        )
        .where(
            BatchMember.batch_id == batch_id,
            BatchMember.is_deleted.is_(False),
        )
    )
    if is_active is not None:
        query = query.where(BatchMember.is_active == is_active)
    if role_id is not None:
        query = query.where(BatchMember.role_id == role_id)

    query = query.offset(skip).limit(limit)
    return db.execute(query).scalars().all()


def get_user_active_batch_memberships(
    db: Session,
    user_id: UUID,
) -> list[BatchMember]:
    query = (
        select(BatchMember)
        .options(
            joinedload(BatchMember.batch),
            joinedload(BatchMember.role),
        )
        .where(
            BatchMember.user_id == user_id,
            BatchMember.is_deleted.is_(False),
            BatchMember.is_active.is_(True),
        )
    )
    return db.execute(query).scalars().all()


def get_employee_membership_in_other_batch(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
    employee_role_id: UUID | None = None,
    current_batch_id: UUID | None = None,
) -> BatchMember | None:
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


def soft_delete_batch_member(
    db: Session,
    member: BatchMember,
    updated_by: UUID | None = None,
) -> BatchMember:
    member.is_deleted = True
    member.is_active = False
    member.deleted_at = datetime.now(UTC)
    member.updated_by = updated_by
    member.updated_at = datetime.now(UTC)
    db.flush()
    return member
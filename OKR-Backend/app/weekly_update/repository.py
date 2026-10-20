from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.weekly_update.models import WeeklyUpdate
from app.weekly_update.schemas import WeeklyUpdateCreate, WeeklyUpdateUpdate


def create_weekly_update(
    db: Session,
    okr_id: UUID,
    update_data: WeeklyUpdateCreate,
    created_by: UUID | None = None,
) -> WeeklyUpdate:
    """
    Create a new weekly update record for an OKR.
    """
    weekly_update = WeeklyUpdate(
        okr_id=okr_id,
        week_number=update_data.week_number,
        progress=update_data.progress,
        remarks=update_data.remarks,
        created_by=created_by,
    )

    db.add(weekly_update)
    db.commit()
    db.refresh(weekly_update)

    return weekly_update


def get_weekly_update_by_id(
    db: Session,
    update_id: UUID,
) -> WeeklyUpdate | None:
    """
    Fetch a single weekly update by its ID.
    """
    query = select(WeeklyUpdate).where(
        WeeklyUpdate.id == update_id,
        WeeklyUpdate.is_deleted.is_(False),
    )

    return db.execute(query).scalar_one_or_none()


def get_weekly_update_by_okr_and_week(
    db: Session,
    okr_id: UUID,
    week_number: int,
) -> WeeklyUpdate | None:
    """
    Fetch a weekly update by OKR ID and week number to prevent duplicate entries.
    """
    query = select(WeeklyUpdate).where(
        WeeklyUpdate.okr_id == okr_id,
        WeeklyUpdate.week_number == week_number,
        WeeklyUpdate.is_deleted.is_(False),
    )

    return db.execute(query).scalar_one_or_none()


from app.common.query import validate_and_apply_sorting

ALLOWED_WEEKLY_UPDATE_SORT_FIELDS = {
    "week_number": WeeklyUpdate.week_number,
    "progress": WeeklyUpdate.progress,
    "created_at": WeeklyUpdate.created_at,
    "updated_at": WeeklyUpdate.updated_at,
}


def get_weekly_updates_by_okr(
    db: Session,
    okr_id: UUID,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    min_progress: float | None = None,
    max_progress: float | None = None,
    sort_by: str | None = "week_number",
    sort_order: str | None = "desc",
):
    """
    Fetch paginated weekly updates for a specific OKR with search, range filters, and sorting.
    """
    base_query = select(WeeklyUpdate).where(
        WeeklyUpdate.okr_id == okr_id,
        WeeklyUpdate.is_deleted.is_(False),
    )

    if search:
        base_query = base_query.where(WeeklyUpdate.remarks.ilike(f"%{search}%"))

    if min_progress is not None:
        base_query = base_query.where(WeeklyUpdate.progress >= min_progress)

    if max_progress is not None:
        base_query = base_query.where(WeeklyUpdate.progress <= max_progress)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = db.execute(count_query).scalar() or 0

    base_query = validate_and_apply_sorting(
        query=base_query,
        model=WeeklyUpdate,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_WEEKLY_UPDATE_SORT_FIELDS,
        default_sort_column=WeeklyUpdate.week_number,
    )

    query = base_query.offset((page - 1) * size).limit(size)

    results = db.execute(query).scalars().all()

    return list(results), total


def update_weekly_update(
    db: Session,
    weekly_update: WeeklyUpdate,
    update_data: WeeklyUpdateUpdate,
    updated_by: UUID | None = None,
) -> WeeklyUpdate:
    """
    Update an existing weekly update record.
    """
    changes = update_data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(weekly_update, field, value)

    weekly_update.updated_by = updated_by
    weekly_update.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(weekly_update)

    return weekly_update


def soft_delete_weekly_update(
    db: Session,
    weekly_update: WeeklyUpdate,
    deleted_by: UUID | None = None,
) -> WeeklyUpdate:
    """
    Soft delete a weekly update record.
    """
    weekly_update.is_deleted = True
    weekly_update.is_active = False
    weekly_update.deleted_at = datetime.now(UTC)
    weekly_update.updated_by = deleted_by

    db.commit()
    db.refresh(weekly_update)

    return weekly_update

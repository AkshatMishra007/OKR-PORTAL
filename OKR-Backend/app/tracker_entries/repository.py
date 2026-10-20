from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.tracker_entries.models import TrackerEntry
from app.tracker_entries.schemas import (
    TrackerEntryCreate,
    TrackerEntryUpdate,
)


def create_tracker_entry(
    db: Session,
    okr_id: UUID,
    entry_data: TrackerEntryCreate,
    created_by: UUID | None = None,
) -> TrackerEntry:
    """
    Create a new tracker entry for an OKR.
    """
    tracker_entry = TrackerEntry(
        okr_id=okr_id,
        week_start=entry_data.week_start,
        opportunities_received=entry_data.opportunities_received,
        opportunities_completed=entry_data.opportunities_completed,
        created_by=created_by,
    )

    db.add(tracker_entry)
    db.commit()
    db.refresh(tracker_entry)

    return tracker_entry


def get_tracker_entry_by_id(
    db: Session,
    entry_id: UUID,
) -> TrackerEntry | None:
    """
    Fetch a single tracker entry by ID with eager-loaded OKR relationship.
    """
    query = (
        select(TrackerEntry)
        .options(joinedload(TrackerEntry.okr))
        .where(
            TrackerEntry.id == entry_id,
            TrackerEntry.is_deleted.is_(False),
        )
    )

    return db.execute(query).scalar_one_or_none()


def get_tracker_entry_by_okr_and_week(
    db: Session,
    okr_id: UUID,
    week_start: date,
) -> TrackerEntry | None:
    """
    Fetch a tracker entry by OKR ID and week_start date.
    """
    query = (
        select(TrackerEntry)
        .options(joinedload(TrackerEntry.okr))
        .where(
            TrackerEntry.okr_id == okr_id,
            TrackerEntry.week_start == week_start,
            TrackerEntry.is_deleted.is_(False),
        )
    )

    return db.execute(query).scalar_one_or_none()


from app.common.query import validate_and_apply_sorting

ALLOWED_TRACKER_SORT_FIELDS = {
    "week_start": TrackerEntry.week_start,
    "opportunities_received": TrackerEntry.opportunities_received,
    "opportunities_completed": TrackerEntry.opportunities_completed,
    "created_at": TrackerEntry.created_at,
    "updated_at": TrackerEntry.updated_at,
}


def get_tracker_entries_by_okr(
    db: Session,
    okr_id: UUID,
    page: int = 1,
    size: int = 20,
    min_received: int | None = None,
    max_received: int | None = None,
    min_completed: int | None = None,
    max_completed: int | None = None,
    sort_by: str | None = "week_start",
    sort_order: str | None = "desc",
) -> tuple[list[TrackerEntry], int]:
    """
    Fetch paginated tracker entries for a specific OKR with range filters and sorting.
    """
    base_query = select(TrackerEntry).where(
        TrackerEntry.okr_id == okr_id,
        TrackerEntry.is_deleted.is_(False),
    )

    if min_received is not None:
        base_query = base_query.where(TrackerEntry.opportunities_received >= min_received)

    if max_received is not None:
        base_query = base_query.where(TrackerEntry.opportunities_received <= max_received)

    if min_completed is not None:
        base_query = base_query.where(TrackerEntry.opportunities_completed >= min_completed)

    if max_completed is not None:
        base_query = base_query.where(TrackerEntry.opportunities_completed <= max_completed)

    count_query = select(func.count()).select_from(base_query.subquery())

    total = db.execute(count_query).scalar() or 0

    base_query = validate_and_apply_sorting(
        query=base_query,
        model=TrackerEntry,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_TRACKER_SORT_FIELDS,
        default_sort_column=TrackerEntry.week_start,
    )

    query = (
        base_query.options(joinedload(TrackerEntry.okr))
        .offset((page - 1) * size)
        .limit(size)
    )

    results = db.execute(query).scalars().all()

    return list(results), total


def update_tracker_entry(
    db: Session,
    tracker_entry: TrackerEntry,
    entry_data: TrackerEntryUpdate,
    updated_by: UUID | None = None,
) -> TrackerEntry:
    """
    Update an existing tracker entry.
    """
    changes = entry_data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(
            tracker_entry,
            field,
            value,
        )

    tracker_entry.updated_by = updated_by
    tracker_entry.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(tracker_entry)

    return tracker_entry


def soft_delete_tracker_entry(
    db: Session,
    tracker_entry: TrackerEntry,
    deleted_by: UUID | None = None,
) -> TrackerEntry:
    """
    Soft delete a tracker entry.
    """
    tracker_entry.is_deleted = True
    tracker_entry.is_active = False
    tracker_entry.deleted_at = datetime.now(UTC)
    tracker_entry.updated_by = deleted_by

    db.commit()
    db.refresh(tracker_entry)

    return tracker_entry


def get_tracker_aggregate_by_okr(
    db: Session,
    okr_id: UUID,
) -> dict:
    """
    Efficiently aggregate total opportunities_received and opportunities_completed
    for a specific OKR (filtering out deleted entries).
    """
    query = (
        select(
            func.coalesce(func.sum(TrackerEntry.opportunities_received), 0).label("total_received"),
            func.coalesce(func.sum(TrackerEntry.opportunities_completed), 0).label("total_completed"),
        )
        .where(
            TrackerEntry.okr_id == okr_id,
            TrackerEntry.is_deleted.is_(False),
        )
    )

    result = db.execute(query).first()
    if result:
        return {
            "total_opportunities_received": int(result.total_received or 0),
            "total_opportunities_completed": int(result.total_completed or 0),
        }
    return {
        "total_opportunities_received": 0,
        "total_opportunities_completed": 0,
    }


def get_tracker_aggregates_for_okrs(
    db: Session,
    okr_ids: list[UUID],
) -> dict[UUID, dict]:
    """
    Bulk aggregate tracker metrics for a list of OKR IDs in a single query (prevents N+1 overhead).
    """
    if not okr_ids:
        return {}

    query = (
        select(
            TrackerEntry.okr_id,
            func.coalesce(func.sum(TrackerEntry.opportunities_received), 0).label("total_received"),
            func.coalesce(func.sum(TrackerEntry.opportunities_completed), 0).label("total_completed"),
        )
        .where(
            TrackerEntry.okr_id.in_(okr_ids),
            TrackerEntry.is_deleted.is_(False),
        )
        .group_by(TrackerEntry.okr_id)
    )

    results = db.execute(query).all()
    mapping = {
        row.okr_id: {
            "total_opportunities_received": int(row.total_received or 0),
            "total_opportunities_completed": int(row.total_completed or 0),
        }
        for row in results
    }

    return mapping


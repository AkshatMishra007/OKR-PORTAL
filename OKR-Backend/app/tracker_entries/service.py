import re
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from app.batches.models import BatchStatus
from app.common.exceptions import (
    AppException,
    OKRNotFoundException,
    TrackerEntryAlreadyExistsException,
    TrackerEntryNotFoundException,
)
from app.my_okr import repository as okr_repository
from app.okr_logs.models import OkrLog
from app.tracker_entries import repository as tracker_repository
from app.tracker_entries.models import TrackerEntry
from app.tracker_entries.schemas import TrackerEntryCreate, TrackerEntryUpdate


def parse_target_percentage(target_str: str | None) -> float | None:
    """
    Safely parse target string (e.g. '80', '80%', '80 %', '100 opportunities') into numeric value.
    Returns float value if a valid number is found, or None if target is empty/non-numeric.
    """
    if not target_str:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", str(target_str))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def calculate_expected_time_progress(
    start_date: date | None,
    end_date: date | None,
    target_date: date | None = None,
) -> float:
    """
    Calculate expected time progress percentage based on elapsed batch days.
    Safely returns 0.0% if batch has not started, and 100.0% if batch has ended.
    """
    if not start_date or not end_date or end_date <= start_date:
        return 0.0

    ref_date = target_date or date.today()

    if ref_date <= start_date:
        return 0.0
    if ref_date >= end_date:
        return 100.0

    total_days = (end_date - start_date).days
    elapsed_days = (ref_date - start_date).days

    progress = (elapsed_days / total_days) * 100.0
    return round(min(max(progress, 0.0), 100.0), 2)


def calculate_weekly_efficiency(
    opportunities_received: int,
    opportunities_completed: int,
) -> float | None:
    """
    Calculate weekly completion efficiency percentage safely avoiding division by zero.
    """
    if opportunities_received <= 0:
        return 0.0
    efficiency = (opportunities_completed / opportunities_received) * 100.0
    return round(efficiency, 2)


def calculate_okr_progress(
    okr,
    db: Session,
    agg_data: dict | None = None,
) -> dict:
    """
    Calculate quarterly progress and tracker metrics for an OKR.
    Handles zero target, unparseable target, overachievement, and expected time progress.
    """
    if agg_data is None:
        agg_data = tracker_repository.get_tracker_aggregate_by_okr(db=db, okr_id=okr.id)

    total_received = agg_data.get("total_opportunities_received", 0)
    total_completed = agg_data.get("total_opportunities_completed", 0)

    parsed_target = parse_target_percentage(okr.target)

    if parsed_target is None or parsed_target <= 0:
        raw_progress = 0.0
        display_progress = 0.0
    else:
        raw_progress = round((total_completed / parsed_target) * 100.0, 2)
        display_progress = round(min(raw_progress, 100.0), 2)

    start_date = okr.batch.start_date if okr and okr.batch else None
    end_date = okr.batch.end_date if okr and okr.batch else None

    time_progress = calculate_expected_time_progress(
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "total_opportunities_received": total_received,
        "total_opportunities_completed": total_completed,
        "parsed_target": parsed_target,
        "progress_percentage": raw_progress,
        "display_progress_percentage": display_progress,
        "expected_time_progress_percentage": time_progress,
    }


from app.my_okr.authorization import authorize_okr_action


def _get_weekly_no(okr, week_start: date) -> int:
    if okr and getattr(okr, "batch", None):
        start_date = getattr(okr.batch, "start_date", None)
        if isinstance(start_date, date):
            days_diff = (week_start - start_date).days
            if days_diff >= 0:
                return (days_diff // 7) + 1
    return week_start.isocalendar().week


class TrackerEntryService:

    def __init__(self, db: Session):
        self.db = db

    def create_tracker_entry(
        self,
        okr_id: UUID,
        entry_data: TrackerEntryCreate,
        current_user,
    ) -> TrackerEntry:
        """
        Create a new tracker entry for an OKR after checking parent OKR authorization.
        """
        okr = okr_repository.get_okr_by_id(
            db=self.db,
            okr_id=okr_id,
        )
        if not okr:
            raise OKRNotFoundException("OKR not found.")
        if okr.batch and (okr.batch.status == BatchStatus.CLOSED or okr.batch.status == "CLOSED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify data because the {okr.batch.name} batch is closed and read-only.",
            )

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=okr_id,
                action="update",
            )

        if not okr.tracker_enabled:
            raise AppException("Tracker is not enabled for this OKR.")

        # existing_entry = tracker_repository.get_tracker_entry_by_okr_and_week(
        #     db=self.db,
        #     okr_id=okr_id,
        #     week_start=entry_data.week_start,
        # )
        # if existing_entry:
        #     raise TrackerEntryAlreadyExistsException(
        #         "A tracker entry for this week start date already exists for this OKR."
        #     )

        entry = tracker_repository.create_tracker_entry(
            db=self.db,
            okr_id=okr_id,
            entry_data=entry_data,
            created_by=current_user.id if current_user else None,
        )

        user_id = getattr(current_user, "id", None)
        if user_id and isinstance(user_id, (UUID, str)):
            weekly_no = _get_weekly_no(okr, entry_data.week_start)
            okr_log = OkrLog(
                weekly_no=weekly_no,
                current_user=user_id,
                datetime=datetime.now(UTC),
                created_by=user_id,
            )
            self.db.add(okr_log)
            self.db.commit()

        return entry

    def get_tracker_entry(
        self,
        entry_id: UUID,
        current_user=None,
    ) -> TrackerEntry:
        """
        Fetch a single tracker entry by ID.
        """
        entry = tracker_repository.get_tracker_entry_by_id(
            db=self.db,
            entry_id=entry_id,
        )
        if not entry:
            raise TrackerEntryNotFoundException("Tracker entry not found.")

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=entry.okr_id,
                action="view",
            )

        return entry

    def get_tracker_entries_for_okr(
        self,
        okr_id: UUID,
        page: int = 1,
        size: int = 20,
        min_received: int | None = None,
        max_received: int | None = None,
        min_completed: int | None = None,
        max_completed: int | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        current_user=None,
    ) -> dict:
        """
        Fetch paginated tracker entries for a specific OKR.
        """
        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=okr_id,
                action="view",
            )
        else:
            okr = okr_repository.get_okr_by_id(
                db=self.db,
                okr_id=okr_id,
            )
            if not okr:
                raise OKRNotFoundException("OKR not found.")

        get_kwargs = {
            "page": page,
            "size": size,
        }
        if min_received is not None:
            get_kwargs["min_received"] = min_received
        if max_received is not None:
            get_kwargs["max_received"] = max_received
        if min_completed is not None:
            get_kwargs["min_completed"] = min_completed
        if max_completed is not None:
            get_kwargs["max_completed"] = max_completed
        if sort_by is not None:
            get_kwargs["sort_by"] = sort_by
        if sort_order is not None:
            get_kwargs["sort_order"] = sort_order

        entries, total = tracker_repository.get_tracker_entries_by_okr(
            db=self.db,
            okr_id=okr_id,
            **get_kwargs,
        )

        total_pages = (total + size - 1) // size if total > 0 else 1

        return {
            "data": entries,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    def update_tracker_entry(
        self,
        entry_id: UUID,
        entry_data: TrackerEntryUpdate,
        current_user,
    ) -> TrackerEntry:
        """
        Update an existing tracker entry.
        """
        entry = tracker_repository.get_tracker_entry_by_id(
            db=self.db,
            entry_id=entry_id,
        )
        if not entry:
            raise TrackerEntryNotFoundException("Tracker entry not found.")

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=entry.okr_id,
                action="update",
            )

        return tracker_repository.update_tracker_entry(
            db=self.db,
            tracker_entry=entry,
            entry_data=entry_data,
            updated_by=current_user.id if current_user else None,
        )

    def delete_tracker_entry(
        self,
        entry_id: UUID,
        current_user,
    ) -> TrackerEntry:
        """
        Soft delete a tracker entry.
        """
        entry = tracker_repository.get_tracker_entry_by_id(
            db=self.db,
            entry_id=entry_id,
        )
        if not entry:
            raise TrackerEntryNotFoundException("Tracker entry not found.")

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=entry.okr_id,
                action="delete",
            )

        return tracker_repository.soft_delete_tracker_entry(
            db=self.db,
            tracker_entry=entry,
            deleted_by=current_user.id if current_user else None,
        )

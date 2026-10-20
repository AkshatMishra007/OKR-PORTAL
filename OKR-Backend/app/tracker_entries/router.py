from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.tracker_entries.schemas import (
    TrackerEntryCreate,
    TrackerEntryListResponse,
    TrackerEntryResponse,
    TrackerEntryUpdate,
)
from app.tracker_entries.service import TrackerEntryService
from app.users.models import User

router = APIRouter(
    tags=["Tracker Entries"],
)


@router.post(
    "/okrs/{okr_id}/tracker-entries",
    response_model=TrackerEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_tracker_entry(
    okr_id: UUID,
    entry_data: TrackerEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new tracker entry for an OKR.
    """
    service = TrackerEntryService(db)
    return service.create_tracker_entry(
        okr_id=okr_id,
        entry_data=entry_data,
        current_user=current_user,
    )


@router.get(
    "/okrs/{okr_id}/tracker-entries",
    response_model=TrackerEntryListResponse,
)
def get_tracker_entries_for_okr(
    okr_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    min_received: int | None = Query(default=None),
    max_received: int | None = Query(default=None),
    min_completed: int | None = Query(default=None),
    max_completed: int | None = Query(default=None),
    sort_by: str | None = Query(default="week_start"),
    sort_order: str | None = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List paginated tracker entries for a specific OKR.
    """
    service = TrackerEntryService(db)
    return service.get_tracker_entries_for_okr(
        okr_id=okr_id,
        page=page,
        size=size,
        min_received=min_received,
        max_received=max_received,
        min_completed=min_completed,
        max_completed=max_completed,
        sort_by=sort_by,
        sort_order=sort_order,
        current_user=current_user,
    )


@router.get(
    "/tracker-entries/{entry_id}",
    response_model=TrackerEntryResponse,
)
def get_tracker_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch a single tracker entry by ID.
    """
    service = TrackerEntryService(db)
    return service.get_tracker_entry(
        entry_id=entry_id,
        current_user=current_user,
    )


@router.put(
    "/tracker-entries/{entry_id}",
    response_model=TrackerEntryResponse,
)
def update_tracker_entry(
    entry_id: UUID,
    entry_data: TrackerEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing tracker entry.
    """
    service = TrackerEntryService(db)
    return service.update_tracker_entry(
        entry_id=entry_id,
        entry_data=entry_data,
        current_user=current_user,
    )


@router.delete(
    "/tracker-entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tracker_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a tracker entry.
    """
    service = TrackerEntryService(db)
    service.delete_tracker_entry(
        entry_id=entry_id,
        current_user=current_user,
    )
    return None

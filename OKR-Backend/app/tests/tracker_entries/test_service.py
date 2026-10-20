import datetime
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import (
    AppException,
    OKRNotFoundException,
    TrackerEntryAlreadyExistsException,
    TrackerEntryNotFoundException,
)
from app.tracker_entries.schemas import TrackerEntryCreate, TrackerEntryUpdate
from app.tracker_entries.service import TrackerEntryService, parse_target_percentage


@patch("app.tracker_entries.service.tracker_repository.create_tracker_entry")
@patch("app.tracker_entries.service.tracker_repository.get_tracker_entry_by_okr_and_week")
@patch("app.tracker_entries.service.okr_repository.get_okr_by_id")
def test_create_tracker_entry_success(
    mock_get_okr,
    mock_get_existing,
    mock_create_entry,
):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    okr_id = uuid.uuid4()
    week_start = datetime.date(2026, 8, 3)

    entry_data = TrackerEntryCreate(
        week_start=week_start,
        opportunities_received=10,
        opportunities_completed=8,
    )

    mock_get_okr.return_value = MagicMock(id=okr_id, tracker_enabled=True)
    mock_get_existing.return_value = None
    expected_entry = MagicMock(id=uuid.uuid4(), okr_id=okr_id, week_start=week_start)
    mock_create_entry.return_value = expected_entry

    service = TrackerEntryService(db)
    result = service.create_tracker_entry(okr_id, entry_data, current_user)

    assert result == expected_entry
    mock_get_okr.assert_called_once_with(db=db, okr_id=okr_id)
    mock_get_existing.assert_called_once_with(db=db, okr_id=okr_id, week_start=week_start)


@patch("app.tracker_entries.service.okr_repository.get_okr_by_id")
def test_create_tracker_entry_okr_not_found(mock_get_okr):
    db = MagicMock()
    current_user = MagicMock()
    okr_id = uuid.uuid4()

    entry_data = TrackerEntryCreate(
        week_start=datetime.date(2026, 8, 3),
    )
    mock_get_okr.return_value = None

    service = TrackerEntryService(db)

    with pytest.raises(OKRNotFoundException):
        service.create_tracker_entry(okr_id, entry_data, current_user)


@patch("app.tracker_entries.service.okr_repository.get_okr_by_id")
def test_create_tracker_entry_tracker_not_enabled(mock_get_okr):
    db = MagicMock()
    current_user = MagicMock()
    okr_id = uuid.uuid4()

    entry_data = TrackerEntryCreate(
        week_start=datetime.date(2026, 8, 3),
    )
    mock_get_okr.return_value = MagicMock(id=okr_id, tracker_enabled=False)

    service = TrackerEntryService(db)

    with pytest.raises(AppException):
        service.create_tracker_entry(okr_id, entry_data, current_user)


@patch("app.tracker_entries.service.tracker_repository.get_tracker_entry_by_okr_and_week")
@patch("app.tracker_entries.service.okr_repository.get_okr_by_id")
def test_create_tracker_entry_already_exists(mock_get_okr, mock_get_existing):
    db = MagicMock()
    current_user = MagicMock()
    okr_id = uuid.uuid4()
    week_start = datetime.date(2026, 8, 3)

    entry_data = TrackerEntryCreate(
        week_start=week_start,
    )
    mock_get_okr.return_value = MagicMock(id=okr_id, tracker_enabled=True)
    mock_get_existing.return_value = MagicMock()

    service = TrackerEntryService(db)

    with pytest.raises(TrackerEntryAlreadyExistsException):
        service.create_tracker_entry(okr_id, entry_data, current_user)


@patch("app.tracker_entries.service.tracker_repository.get_tracker_entry_by_id")
def test_get_tracker_entry_success(mock_get_by_id):
    db = MagicMock()
    entry_id = uuid.uuid4()
    expected = MagicMock(id=entry_id)
    mock_get_by_id.return_value = expected

    service = TrackerEntryService(db)
    result = service.get_tracker_entry(entry_id)

    assert result == expected


@patch("app.tracker_entries.service.tracker_repository.get_tracker_entry_by_id")
def test_get_tracker_entry_not_found(mock_get_by_id):
    db = MagicMock()
    entry_id = uuid.uuid4()
    mock_get_by_id.return_value = None

    service = TrackerEntryService(db)

    with pytest.raises(TrackerEntryNotFoundException):
        service.get_tracker_entry(entry_id)


@patch("app.tracker_entries.service.tracker_repository.get_tracker_entries_by_okr")
@patch("app.tracker_entries.service.okr_repository.get_okr_by_id")
def test_get_tracker_entries_for_okr_success(mock_get_okr, mock_get_by_okr):
    db = MagicMock()
    okr_id = uuid.uuid4()
    mock_get_okr.return_value = MagicMock(id=okr_id)
    mock_entries = [MagicMock(), MagicMock()]
    mock_get_by_okr.return_value = (mock_entries, 2)

    service = TrackerEntryService(db)
    result = service.get_tracker_entries_for_okr(okr_id, page=1, size=20)

    assert result["data"] == mock_entries
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["size"] == 20
    assert result["pagination"]["total"] == 2


@patch("app.tracker_entries.service.tracker_repository.update_tracker_entry")
@patch("app.tracker_entries.service.tracker_repository.get_tracker_entry_by_id")
def test_update_tracker_entry_success(mock_get_by_id, mock_update):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    entry_id = uuid.uuid4()
    existing_entry = MagicMock(id=entry_id)
    mock_get_by_id.return_value = existing_entry
    updated_result = MagicMock(id=entry_id, opportunities_completed=9)
    mock_update.return_value = updated_result

    entry_data = TrackerEntryUpdate(opportunities_completed=9)
    service = TrackerEntryService(db)
    result = service.update_tracker_entry(entry_id, entry_data, current_user)

    assert result == updated_result


@patch("app.tracker_entries.service.tracker_repository.soft_delete_tracker_entry")
@patch("app.tracker_entries.service.tracker_repository.get_tracker_entry_by_id")
def test_delete_tracker_entry_success(mock_get_by_id, mock_delete):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    entry_id = uuid.uuid4()
    existing_entry = MagicMock(id=entry_id)
    mock_get_by_id.return_value = existing_entry
    mock_delete.return_value = existing_entry

    service = TrackerEntryService(db)
    result = service.delete_tracker_entry(entry_id, current_user)

    assert result == existing_entry


def test_parse_target_percentage():
    assert parse_target_percentage("80") == 80.0
    assert parse_target_percentage("80%") == 80.0
    assert parse_target_percentage("85.5 %") == 85.5
    assert parse_target_percentage("100 opportunities") == 100.0
    assert parse_target_percentage(None) is None
    assert parse_target_percentage("invalid") is None

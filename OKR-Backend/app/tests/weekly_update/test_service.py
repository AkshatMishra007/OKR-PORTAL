import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import (
    OKRNotFoundException,
    WeeklyUpdateAlreadyExistsException,
    WeeklyUpdateNotFoundException,
)
from app.weekly_update.schemas import WeeklyUpdateCreate, WeeklyUpdateUpdate
from app.weekly_update.service import WeeklyUpdateService


@patch("app.weekly_update.service.weekly_update_repository.create_weekly_update")
@patch("app.weekly_update.service.weekly_update_repository.get_weekly_update_by_okr_and_week")
@patch("app.weekly_update.service.okr_repository.get_okr_by_id")
def test_create_weekly_update_success(
    mock_get_okr,
    mock_get_existing,
    mock_create_update,
):
    db = MagicMock()
    current_user = MagicMock()
    current_user.id = uuid.uuid4()
    okr_id = uuid.uuid4()

    update_data = WeeklyUpdateCreate(
        week_number=1,
        progress=50,
        remarks="Good progress",
    )

    mock_get_okr.return_value = MagicMock(id=okr_id)
    mock_get_existing.return_value = None
    expected_update = MagicMock(id=uuid.uuid4(), okr_id=okr_id, week_number=1, progress=50)
    mock_create_update.return_value = expected_update

    service = WeeklyUpdateService(db)
    result = service.create_weekly_update(okr_id, update_data, current_user)

    assert result == expected_update
    mock_get_okr.assert_called_once_with(db=db, okr_id=okr_id)
    mock_get_existing.assert_called_once_with(db=db, okr_id=okr_id, week_number=1)


@patch("app.weekly_update.service.okr_repository.get_okr_by_id")
def test_create_weekly_update_okr_not_found(mock_get_okr):
    db = MagicMock()
    current_user = MagicMock()
    okr_id = uuid.uuid4()

    update_data = WeeklyUpdateCreate(week_number=1, progress=50)
    mock_get_okr.return_value = None

    service = WeeklyUpdateService(db)

    with pytest.raises(OKRNotFoundException):
        service.create_weekly_update(okr_id, update_data, current_user)


@patch("app.weekly_update.service.weekly_update_repository.get_weekly_update_by_okr_and_week")
@patch("app.weekly_update.service.okr_repository.get_okr_by_id")
def test_create_weekly_update_already_exists(mock_get_okr, mock_get_existing):
    db = MagicMock()
    current_user = MagicMock()
    okr_id = uuid.uuid4()

    update_data = WeeklyUpdateCreate(week_number=1, progress=50)
    mock_get_okr.return_value = MagicMock(id=okr_id)
    mock_get_existing.return_value = MagicMock()

    service = WeeklyUpdateService(db)

    with pytest.raises(WeeklyUpdateAlreadyExistsException):
        service.create_weekly_update(okr_id, update_data, current_user)


@patch("app.weekly_update.service.weekly_update_repository.get_weekly_update_by_id")
def test_get_weekly_update_success(mock_get_by_id):
    db = MagicMock()
    update_id = uuid.uuid4()
    expected = MagicMock(id=update_id)
    mock_get_by_id.return_value = expected

    service = WeeklyUpdateService(db)
    result = service.get_weekly_update(update_id)

    assert result == expected


@patch("app.weekly_update.service.weekly_update_repository.get_weekly_update_by_id")
def test_get_weekly_update_not_found(mock_get_by_id):
    db = MagicMock()
    update_id = uuid.uuid4()
    mock_get_by_id.return_value = None

    service = WeeklyUpdateService(db)

    with pytest.raises(WeeklyUpdateNotFoundException):
        service.get_weekly_update(update_id)


@patch("app.weekly_update.service.weekly_update_repository.get_weekly_updates_by_okr")
@patch("app.weekly_update.service.okr_repository.get_okr_by_id")
def test_get_weekly_updates_for_okr_success(mock_get_okr, mock_get_by_okr):
    db = MagicMock()
    okr_id = uuid.uuid4()
    mock_get_okr.return_value = MagicMock(id=okr_id)
    mock_updates = [MagicMock(), MagicMock()]
    mock_get_by_okr.return_value = (mock_updates, 2)

    service = WeeklyUpdateService(db)
    result = service.get_weekly_updates_for_okr(okr_id, page=1, size=20)

    assert result["data"] == mock_updates
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["size"] == 20
    assert result["pagination"]["total"] == 2


@patch("app.weekly_update.service.weekly_update_repository.update_weekly_update")
@patch("app.weekly_update.service.weekly_update_repository.get_weekly_update_by_id")
def test_update_weekly_update_success(mock_get_by_id, mock_update):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    update_id = uuid.uuid4()
    existing_update = MagicMock(id=update_id)
    mock_get_by_id.return_value = existing_update
    updated_result = MagicMock(id=update_id, progress=80)
    mock_update.return_value = updated_result

    update_data = WeeklyUpdateUpdate(progress=80)
    service = WeeklyUpdateService(db)
    result = service.update_weekly_update(update_id, update_data, current_user)

    assert result == updated_result


@patch("app.weekly_update.service.weekly_update_repository.soft_delete_weekly_update")
@patch("app.weekly_update.service.weekly_update_repository.get_weekly_update_by_id")
def test_delete_weekly_update_success(mock_get_by_id, mock_delete):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    update_id = uuid.uuid4()
    existing_update = MagicMock(id=update_id)
    mock_get_by_id.return_value = existing_update
    mock_delete.return_value = existing_update

    service = WeeklyUpdateService(db)
    result = service.delete_weekly_update(update_id, current_user)

    assert result == existing_update

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import (
    FogsHurdleNotFoundException,
    OKRNotFoundException,
)
from app.fogs_hurdles.schemas import FogsHurdleCreate, FogsHurdleUpdate
from app.fogs_hurdles.service import FogsHurdleService


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.create_fogs_hurdle")
@patch("app.fogs_hurdles.service.okr_repository.get_okr_by_id")
def test_create_fogs_hurdle_success(
    mock_get_okr,
    mock_create_fogs_hurdle,
):
    db = MagicMock()
    current_user = MagicMock()
    current_user.id = uuid.uuid4()
    okr_id = uuid.uuid4()

    hurdle_data = FogsHurdleCreate(
        fogs_hurdles="Network delay issue",
        action_points="Escalate to DevOps team",
    )

    mock_get_okr.return_value = MagicMock(id=okr_id)
    expected_record = MagicMock(
        id=uuid.uuid4(),
        okr_id=okr_id,
        fogs_hurdles="Network delay issue",
        action_points="Escalate to DevOps team",
    )
    mock_create_fogs_hurdle.return_value = expected_record

    service = FogsHurdleService(db)
    result = service.create_fogs_hurdle(okr_id, hurdle_data, current_user)

    assert result == expected_record
    mock_get_okr.assert_called_once_with(db=db, okr_id=okr_id)
    mock_create_fogs_hurdle.assert_called_once_with(
        db=db,
        okr_id=okr_id,
        fogs_hurdle_data=hurdle_data,
        created_by=current_user.id,
    )


@patch("app.fogs_hurdles.service.okr_repository.get_okr_by_id")
def test_create_fogs_hurdle_okr_not_found(mock_get_okr):
    db = MagicMock()
    current_user = MagicMock()
    okr_id = uuid.uuid4()

    hurdle_data = FogsHurdleCreate(fogs_hurdles="Budget constraint")
    mock_get_okr.return_value = None

    service = FogsHurdleService(db)

    with pytest.raises(OKRNotFoundException):
        service.create_fogs_hurdle(okr_id, hurdle_data, current_user)


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.get_fogs_hurdle_by_id")
def test_get_fogs_hurdle_success(mock_get_by_id):
    db = MagicMock()
    hurdle_id = uuid.uuid4()
    expected = MagicMock(id=hurdle_id)
    mock_get_by_id.return_value = expected

    service = FogsHurdleService(db)
    result = service.get_fogs_hurdle(hurdle_id)

    assert result == expected
    mock_get_by_id.assert_called_once_with(db=db, fogs_hurdle_id=hurdle_id)


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.get_fogs_hurdle_by_id")
def test_get_fogs_hurdle_not_found(mock_get_by_id):
    db = MagicMock()
    hurdle_id = uuid.uuid4()
    mock_get_by_id.return_value = None

    service = FogsHurdleService(db)

    with pytest.raises(FogsHurdleNotFoundException):
        service.get_fogs_hurdle(hurdle_id)


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.get_fogs_hurdles_by_okr")
@patch("app.fogs_hurdles.service.okr_repository.get_okr_by_id")
def test_get_fogs_hurdles_for_okr_success(mock_get_okr, mock_get_by_okr):
    db = MagicMock()
    okr_id = uuid.uuid4()
    mock_get_okr.return_value = MagicMock(id=okr_id)
    mock_records = [MagicMock(), MagicMock()]
    mock_get_by_okr.return_value = (mock_records, 2)

    service = FogsHurdleService(db)
    result = service.get_fogs_hurdles_for_okr(okr_id, page=1, size=20)

    assert result["data"] == mock_records
    assert result["pagination"] == {"page": 1, "size": 20, "total": 2}


@patch("app.fogs_hurdles.service.okr_repository.get_okr_by_id")
def test_get_fogs_hurdles_for_okr_not_found(mock_get_okr):
    db = MagicMock()
    okr_id = uuid.uuid4()
    mock_get_okr.return_value = None

    service = FogsHurdleService(db)

    with pytest.raises(OKRNotFoundException):
        service.get_fogs_hurdles_for_okr(okr_id, page=1, size=20)


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.update_fogs_hurdle")
@patch("app.fogs_hurdles.service.fogs_hurdle_repository.get_fogs_hurdle_by_id")
def test_update_fogs_hurdle_success(mock_get_by_id, mock_update):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    hurdle_id = uuid.uuid4()
    existing_record = MagicMock(id=hurdle_id)
    mock_get_by_id.return_value = existing_record
    updated_result = MagicMock(id=hurdle_id, fogs_hurdles="Resolved issue")
    mock_update.return_value = updated_result

    update_data = FogsHurdleUpdate(fogs_hurdles="Resolved issue")
    service = FogsHurdleService(db)
    result = service.update_fogs_hurdle(hurdle_id, update_data, current_user)

    assert result == updated_result


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.get_fogs_hurdle_by_id")
def test_update_fogs_hurdle_not_found(mock_get_by_id):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    hurdle_id = uuid.uuid4()
    mock_get_by_id.return_value = None

    update_data = FogsHurdleUpdate(fogs_hurdles="Resolved issue")
    service = FogsHurdleService(db)

    with pytest.raises(FogsHurdleNotFoundException):
        service.update_fogs_hurdle(hurdle_id, update_data, current_user)


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.soft_delete_fogs_hurdle")
@patch("app.fogs_hurdles.service.fogs_hurdle_repository.get_fogs_hurdle_by_id")
def test_delete_fogs_hurdle_success(mock_get_by_id, mock_delete):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    hurdle_id = uuid.uuid4()
    existing_record = MagicMock(id=hurdle_id)
    mock_get_by_id.return_value = existing_record
    mock_delete.return_value = existing_record

    service = FogsHurdleService(db)
    result = service.delete_fogs_hurdle(hurdle_id, current_user)

    assert result == existing_record


@patch("app.fogs_hurdles.service.fogs_hurdle_repository.get_fogs_hurdle_by_id")
def test_delete_fogs_hurdle_not_found(mock_get_by_id):
    db = MagicMock()
    current_user = MagicMock(id=uuid.uuid4())
    hurdle_id = uuid.uuid4()
    mock_get_by_id.return_value = None

    service = FogsHurdleService(db)

    with pytest.raises(FogsHurdleNotFoundException):
        service.delete_fogs_hurdle(hurdle_id, current_user)

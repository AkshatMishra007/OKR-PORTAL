# Tests for OKR Logs Service, Repository, and Schemas.
import uuid
from datetime import UTC, datetime
import pytest
from app.okr_logs.models import OkrLog
from app.okr_logs.schemas import OkrLogCreate, OkrLogResponse
from app.okr_logs import repository as okr_log_repository
from app.okr_logs.service import OkrLogService


def test_create_and_get_okr_log(db_session, test_user):
    service = OkrLogService(db_session)
    log_data = OkrLogCreate(
        weekly_no=5,
        current_user=test_user.id,
        datetime=datetime.now(UTC),
    )
    log = service.create_log(log_data=log_data, current_user=test_user)

    assert log.id is not None
    assert log.weekly_no == 5
    assert log.current_user == test_user.id
    assert log.created_by == test_user.id
    assert log.is_deleted is False

    # Get by user
    user_logs = service.get_logs_by_user(user_id=test_user.id)
    assert len(user_logs) >= 1
    assert any(l.id == log.id for l in user_logs)

    # Get by week
    week_logs = service.get_logs_by_week(weekly_no=5)
    assert len(week_logs) >= 1
    assert any(l.id == log.id for l in week_logs)

    # List logs
    all_logs = service.list_logs(skip=0, limit=10)
    assert len(all_logs) >= 1

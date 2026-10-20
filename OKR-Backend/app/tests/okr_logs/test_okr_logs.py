"""
Test suite for OKR Audit Logs & Activity Tracking (okr_logs).
"""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.batches.models import BatchStatus, MeetingDay, Quarter
from app.batches.schemas import BatchCreate
from app.batches.service import BatchService
from app.common.exceptions import TrackerEntryAlreadyExistsException
from app.my_okr import service as okr_service
from app.my_okr.schemas import OKRCreate
from app.okr_logs.models import OkrLog
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.tracker_entries.schemas import TrackerEntryCreate
from app.tracker_entries.service import TrackerEntryService
from app.users.models import User


@pytest.fixture
def audit_log_test_setup(db_session: Session):
    """
    Setup test organization, active batch, users, and memberships.
    """
    org = Organization(name=f"Audit Test Org {uuid4().hex[:6]}", description="Audit Log Test")
    db_session.add(org)
    db_session.commit()

    role = db_session.query(Role).filter(Role.name == "ORG_ADMIN").first()
    if not role:
        role = Role(name="ORG_ADMIN", description="Org Admin Role")
        db_session.add(role)
        db_session.commit()

    user_a = User(
        username=f"user_a_{uuid4().hex[:6]}",
        email=f"user_a.{uuid4().hex[:6]}@test.local",
        password_hash="passhash123",
        first_name="User",
        last_name="A",
    )
    user_b = User(
        username=f"user_b_{uuid4().hex[:6]}",
        email=f"user_b.{uuid4().hex[:6]}@test.local",
        password_hash="passhash123",
        first_name="User",
        last_name="B",
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()

    batch_service = BatchService(db_session)
    batch = batch_service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="AMJ 2026 Audit",
            year=2026,
            quarter=Quarter.AMJ,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 30),
            meeting_day=MeetingDay.MONDAY,
        ),
        current_user=user_a,
    )
    batch.status = BatchStatus.ACTIVE
    db_session.commit()

    member_a = OrganizationMember(
        organization_id=org.id,
        user_id=user_a.id,
        role_id=role.id,
        batch_id=batch.id,
    )
    member_b = OrganizationMember(
        organization_id=org.id,
        user_id=user_b.id,
        role_id=role.id,
        batch_id=batch.id,
    )
    db_session.add_all([member_a, member_b])
    db_session.commit()

    return {
        "org": org,
        "batch": batch,
        "user_a": user_a,
        "user_b": user_b,
        "member_a": member_a,
        "member_b": member_b,
    }


def test_successful_tracker_entry_creates_okr_log(db_session: Session, audit_log_test_setup: dict):
    d = audit_log_test_setup
    user_a = d["user_a"]
    member_a = d["member_a"]
    batch = d["batch"]

    okr = okr_service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member_a.id,
            objective="Audit Log Target OKR",
            target="100 deals",
            okr_type="PROFESSIONAL",
            tracker_enabled=True,
        ),
        user_a,
    )

    tr_service = TrackerEntryService(db_session)

    # Count logs before
    initial_log_count = db_session.query(OkrLog).count()

    entry = tr_service.create_tracker_entry(
        okr_id=okr.id,
        entry_data=TrackerEntryCreate(
            week_start=date(2026, 4, 6),
            opportunities_received=10,
            opportunities_completed=8,
        ),
        current_user=user_a,
    )

    assert entry is not None

    logs = db_session.query(OkrLog).all()
    assert len(logs) == initial_log_count + 1

    latest_log = logs[-1]
    assert latest_log.weekly_no == 1
    assert latest_log.current_user == user_a.id
    assert latest_log.datetime is not None


def test_failed_tracker_entry_creates_no_log(db_session: Session, audit_log_test_setup: dict):
    d = audit_log_test_setup
    user_a = d["user_a"]
    member_a = d["member_a"]
    batch = d["batch"]

    okr = okr_service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member_a.id,
            objective="Audit Log Failed Entry OKR",
            target="50 deals",
            okr_type="PROFESSIONAL",
            tracker_enabled=True,
        ),
        user_a,
    )

    tr_service = TrackerEntryService(db_session)

    # 1. First entry succeeds
    tr_service.create_tracker_entry(
        okr_id=okr.id,
        entry_data=TrackerEntryCreate(
            week_start=date(2026, 4, 6),
            opportunities_received=10,
            opportunities_completed=5,
        ),
        current_user=user_a,
    )

    log_count_after_first = db_session.query(OkrLog).count()

    # 2. Duplicate entry fails with TrackerEntryAlreadyExistsException
    with pytest.raises(TrackerEntryAlreadyExistsException):
        tr_service.create_tracker_entry(
            okr_id=okr.id,
            entry_data=TrackerEntryCreate(
                week_start=date(2026, 4, 6),
                opportunities_received=15,
                opportunities_completed=10,
            ),
            current_user=user_a,
        )

    # Verify no new log record was created on failure
    log_count_after_failure = db_session.query(OkrLog).count()
    assert log_count_after_failure == log_count_after_first


def test_user_isolation_in_audit_log(db_session: Session, audit_log_test_setup: dict):
    d = audit_log_test_setup
    user_b = d["user_b"]
    member_b = d["member_b"]
    batch = d["batch"]

    okr = okr_service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member_b.id,
            objective="User B OKR",
            target="80 deals",
            okr_type="PROFESSIONAL",
            tracker_enabled=True,
        ),
        user_b,
    )

    tr_service = TrackerEntryService(db_session)

    tr_service.create_tracker_entry(
        okr_id=okr.id,
        entry_data=TrackerEntryCreate(
            week_start=date(2026, 4, 13),
            opportunities_received=20,
            opportunities_completed=15,
        ),
        current_user=user_b,
    )

    latest_log = db_session.query(OkrLog).order_by(OkrLog.created_at.desc()).first()
    assert latest_log is not None
    assert latest_log.current_user == user_b.id
    assert latest_log.weekly_no == 2

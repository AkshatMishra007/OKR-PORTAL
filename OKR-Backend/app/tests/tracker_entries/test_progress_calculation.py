"""
Comprehensive test suite for My-OKR Quarterly Progress & Tracker Calculation.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.batches.models import Batch, BatchStatus, MeetingDay, Quarter
from app.batches.schemas import BatchCreate
from app.batches.service import BatchService
from app.my_okr import service as okr_service
from app.my_okr.models import OKR
from app.my_okr.schemas import OKRCreate
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.tracker_entries.models import TrackerEntry
from app.tracker_entries import repository as tracker_repo
from app.tracker_entries.schemas import TrackerEntryCreate
from app.tracker_entries.service import (
    TrackerEntryService,
    calculate_expected_time_progress,
    calculate_okr_progress,
    calculate_weekly_efficiency,
    parse_target_percentage,
)
from app.users.models import User


@pytest.fixture
def progress_test_setup(db_session: Session):
    """
    Setup test organization, active batch, closed batch, users, and memberships.
    """
    org = Organization(name=f"Progress Test Org {uuid4().hex[:6]}", description="Progress Test")
    db_session.add(org)
    db_session.commit()

    role = db_session.query(Role).filter(Role.name == "ORG_ADMIN").first()
    if not role:
        role = Role(name="ORG_ADMIN", description="Org Admin Role")
        db_session.add(role)
        db_session.commit()

    user = User(
        username=f"prog_user_{uuid4().hex[:6]}",
        email=f"prog.{uuid4().hex[:6]}@test.local",
        password_hash="passhash123",
        first_name="Progress",
        last_name="Tester",
    )
    db_session.add(user)
    db_session.commit()

    batch_service = BatchService(db_session)
    amj_batch = batch_service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="AMJ 2026",
            year=2026,
            quarter=Quarter.AMJ,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 30),
            meeting_day=MeetingDay.MONDAY,
        ),
        current_user=user,
    )
    amj_batch.status = BatchStatus.ACTIVE
    db_session.commit()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(member)
    db_session.commit()

    return {
        "org": org,
        "batch": amj_batch,
        "user": user,
        "member": member,
    }


def test_target_parsing():
    assert parse_target_percentage("100") == 100.0
    assert parse_target_percentage("80%") == 80.0
    assert parse_target_percentage("100 opportunities") == 100.0
    assert parse_target_percentage("150.5 deals") == 150.5
    assert parse_target_percentage("") is None
    assert parse_target_percentage("No target") is None


def test_tracker_aggregation_and_filtering(db_session: Session, progress_test_setup: dict):
    d = progress_test_setup
    member = d["member"]
    user = d["user"]
    batch = d["batch"]

    # 1. Create OKR A and OKR B
    okr_a = okr_service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member.id,
            objective="OKR A Progress Target",
            target="100 deals",
            okr_type="PROFESSIONAL",
            tracker_enabled=True,
        ),
        user,
    )

    okr_b = okr_service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member.id,
            objective="OKR B Isolation Target",
            target="200 deals",
            okr_type="PROFESSIONAL",
            tracker_enabled=True,
        ),
        user,
    )

    tr_service = TrackerEntryService(db_session)

    # 2. Add entries for OKR A
    tr1 = tr_service.create_tracker_entry(okr_a.id, TrackerEntryCreate(week_start=date(2026, 4, 6), opportunities_received=15, opportunities_completed=10), user)
    tr2 = tr_service.create_tracker_entry(okr_a.id, TrackerEntryCreate(week_start=date(2026, 4, 13), opportunities_received=20, opportunities_completed=15), user)

    # 3. Add soft-deleted entry for OKR A
    tr_deleted = tr_service.create_tracker_entry(okr_a.id, TrackerEntryCreate(week_start=date(2026, 4, 20), opportunities_received=100, opportunities_completed=100), user)
    tr_service.delete_tracker_entry(tr_deleted.id, user)

    # 4. Add entry for OKR B (to test isolation)
    tr_service.create_tracker_entry(okr_b.id, TrackerEntryCreate(week_start=date(2026, 4, 6), opportunities_received=50, opportunities_completed=40), user)

    # 5. Aggregate OKR A
    agg_a = tracker_repo.get_tracker_aggregate_by_okr(db_session, okr_a.id)
    assert agg_a["total_opportunities_received"] == 35  # 15 + 20
    assert agg_a["total_opportunities_completed"] == 25  # 10 + 15

    # 6. Bulk aggregate
    bulk_agg = tracker_repo.get_tracker_aggregates_for_okrs(db_session, [okr_a.id, okr_b.id])
    assert bulk_agg[okr_a.id]["total_opportunities_completed"] == 25
    assert bulk_agg[okr_b.id]["total_opportunities_completed"] == 40


def test_okr_progress_calculation(db_session: Session, progress_test_setup: dict):
    d = progress_test_setup
    member = d["member"]
    user = d["user"]
    batch = d["batch"]
    tr_service = TrackerEntryService(db_session)

    # 1. No entries -> 0% progress
    okr_empty = okr_service.create_okr(db_session, OKRCreate(batch_id=batch.id, assigned_to=member.id, objective="Empty OKR", target="100", okr_type="PROFESSIONAL", tracker_enabled=True), user)
    prog_empty = calculate_okr_progress(okr_empty, db_session)
    assert prog_empty["progress_percentage"] == 0.0
    assert prog_empty["display_progress_percentage"] == 0.0

    # 2. Partial progress (55%)
    okr_partial = okr_service.create_okr(db_session, OKRCreate(batch_id=batch.id, assigned_to=member.id, objective="Partial OKR", target="100", okr_type="PROFESSIONAL", tracker_enabled=True), user)
    tr_service.create_tracker_entry(okr_partial.id, TrackerEntryCreate(week_start=date(2026, 4, 6), opportunities_received=30, opportunities_completed=25), user)
    tr_service.create_tracker_entry(okr_partial.id, TrackerEntryCreate(week_start=date(2026, 4, 13), opportunities_received=40, opportunities_completed=30), user)

    prog_partial = calculate_okr_progress(okr_partial, db_session)
    assert prog_partial["total_opportunities_completed"] == 55
    assert prog_partial["progress_percentage"] == 55.0
    assert prog_partial["display_progress_percentage"] == 55.0

    # 3. Overachievement (120% raw vs 100% display)
    okr_over = okr_service.create_okr(db_session, OKRCreate(batch_id=batch.id, assigned_to=member.id, objective="Overachieved OKR", target="100", okr_type="PROFESSIONAL", tracker_enabled=True), user)
    tr_service.create_tracker_entry(okr_over.id, TrackerEntryCreate(week_start=date(2026, 4, 6), opportunities_received=150, opportunities_completed=120), user)

    prog_over = calculate_okr_progress(okr_over, db_session)
    assert prog_over["progress_percentage"] == 120.0
    assert prog_over["display_progress_percentage"] == 100.0

    # 4. Zero or non-numeric target
    okr_zero = okr_service.create_okr(db_session, OKRCreate(batch_id=batch.id, assigned_to=member.id, objective="Zero Target OKR", target="0", okr_type="STANDARD", tracker_enabled=False), user)
    prog_zero = calculate_okr_progress(okr_zero, db_session)
    assert prog_zero["progress_percentage"] == 0.0
    assert prog_zero["display_progress_percentage"] == 0.0


def test_weekly_completion_efficiency():
    assert calculate_weekly_efficiency(20, 10) == 50.0
    assert calculate_weekly_efficiency(15, 15) == 100.0
    assert calculate_weekly_efficiency(0, 0) == 0.0
    assert calculate_weekly_efficiency(0, 5) == 0.0
    assert calculate_weekly_efficiency(10, 12) == 120.0


def test_expected_time_progress():
    start = date(2026, 4, 1)
    end = date(2026, 6, 30)

    # Before start -> 0%
    assert calculate_expected_time_progress(start, end, target_date=date(2026, 3, 15)) == 0.0

    # Mid batch -> ~50%
    mid_progress = calculate_expected_time_progress(start, end, target_date=date(2026, 5, 16))
    assert 48.0 <= mid_progress <= 52.0

    # At or after end -> 100%
    assert calculate_expected_time_progress(start, end, target_date=date(2026, 7, 1)) == 100.0


def test_closed_batch_progress_preservation(db_session: Session, progress_test_setup: dict):
    """
    Verify that when a batch is closed, progress calculations continue to work on historical data.
    """
    d = progress_test_setup
    member = d["member"]
    user = d["user"]
    batch = d["batch"]
    batch_service = BatchService(db_session)
    tr_service = TrackerEntryService(db_session)

    okr = okr_service.create_okr(db_session, OKRCreate(batch_id=batch.id, assigned_to=member.id, objective="Closed Batch OKR", target="100", okr_type="PROFESSIONAL", tracker_enabled=True), user)
    tr_service.create_tracker_entry(okr.id, TrackerEntryCreate(week_start=date(2026, 4, 6), opportunities_received=30, opportunities_completed=20), user)
    tr_service.create_tracker_entry(okr.id, TrackerEntryCreate(week_start=date(2026, 4, 13), opportunities_received=40, opportunities_completed=40), user)

    # Close Batch
    batch_service.close_batch(batch.id, user)

    reloaded_okr = okr_service.get_okr(db_session, okr.id)
    assert reloaded_okr.total_opportunities_completed == 60
    assert reloaded_okr.progress_percentage == 60.0
    assert reloaded_okr.display_progress_percentage == 60.0

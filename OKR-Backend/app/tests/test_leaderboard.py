import uuid
import pytest
from datetime import datetime, UTC
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.auth.dependencies import get_current_user
from app.leaderboard.service import (
    _get_okr_overall_progress,
    get_award,
    get_leaderboard_service,
)
from app.leaderboard.schemas import LeaderboardResponse
from app.organizations.models import Organization
from app.organization_members.models import OrganizationMember
from app.batches.models import Batch, Quarter, MeetingDay, BatchStatus
from app.my_okr.models import OKR
from app.tracker_entries.models import TrackerEntry
from app.weekly_update.models import WeeklyUpdate
from app.users.models import User
from app.rbac.models import Role

client = TestClient(app)


# =========================================================
# Unit Tests for Helper Functions
# =========================================================

def test_get_award_tiers():
    assert get_award(100.0) == "Gladiator"
    assert get_award(90.0) == "Gladiator"
    assert get_award(89.9) == "Platinum"
    assert get_award(80.0) == "Platinum"
    assert get_award(79.9) == "Gold"
    assert get_award(60.0) == "Gold"
    assert get_award(59.9) == "Bronze"
    assert get_award(0.0) == "Bronze"


# =========================================================
# Regression Tests for Hybrid Progress Calculation
# =========================================================

def test_regression_tracker_enabled_above_100_capped():
    """Tracker-enabled OKR with progress above 100% -> capped at 100%."""
    class MockOKR:
        tracker_enabled = True
        display_progress_percentage = 135.0

    assert _get_okr_overall_progress(MockOKR()) == 100.0


def test_regression_tracker_disabled_latest_weekly_progress_85():
    """Tracker-disabled OKR with latest weekly progress of 85% -> 85%."""
    class MockUpdate:
        def __init__(self, progress, week, updated_at=None, is_deleted=False):
            self.progress = progress
            self.week_number = week
            self.updated_at = updated_at
            self.created_at = updated_at
            self.is_deleted = is_deleted

    class MockOKR:
        tracker_enabled = False
        weekly_updates = [
            MockUpdate(progress=50, week=1, updated_at=datetime(2026, 1, 10)),
            MockUpdate(progress=85, week=2, updated_at=datetime(2026, 1, 17)),
            MockUpdate(progress=99, week=3, updated_at=datetime(2026, 1, 24), is_deleted=True),
        ]

    assert _get_okr_overall_progress(MockOKR()) == 85.0


def test_regression_user_two_okrs_100_and_85_average_92_5(db_session):
    """User with two OKRs at 100% and 85% -> score 92.5%."""
    org = Organization(id=uuid.uuid4(), name="Hybrid Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    batch = Batch(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Hybrid Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=datetime(2026, 1, 1).date(),
        end_date=datetime(2026, 3, 31).date(),
        meeting_day=MeetingDay.MONDAY,
        status=BatchStatus.ACTIVE,
        is_deleted=False,
    )
    db_session.add_all([org, role, batch])

    user = User(
        id=uuid.uuid4(),
        username="suyash_test",
        email="suyash@test.com",
        password_hash="h",
        first_name="Suyash",
        last_name="Gaur",
        is_deleted=False,
    )
    db_session.add(user)

    mem = OrganizationMember(
        id=uuid.uuid4(),
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
        is_deleted=False,
        is_active=True,
    )
    db_session.add(mem)

    # OKR 1: Tracker-enabled (100% completed)
    okr1 = OKR(
        id=uuid.uuid4(),
        batch_id=batch.id,
        assigned_to=mem.id,
        objective="Deals (Tracker)",
        target="100",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
        is_deleted=False,
    )
    # OKR 2: Tracker-disabled (Weekly updates: 85%)
    okr2 = OKR(
        id=uuid.uuid4(),
        batch_id=batch.id,
        assigned_to=mem.id,
        objective="Leads (Manual)",
        target="20",
        okr_type="PROFESSIONAL",
        tracker_enabled=False,
        is_deleted=False,
    )
    db_session.add_all([okr1, okr2])

    t1 = TrackerEntry(
        id=uuid.uuid4(),
        okr_id=okr1.id,
        week_start=datetime(2026, 1, 1).date(),
        opportunities_received=100,
        opportunities_completed=100,
        is_deleted=False,
    )
    w2 = WeeklyUpdate(
        id=uuid.uuid4(),
        okr_id=okr2.id,
        week_number=1,
        progress=85,
        is_deleted=False,
    )
    db_session.add_all([t1, w2])
    db_session.commit()

    response = get_leaderboard_service(db=db_session, current_user_id=user.id)
    assert len(response.items) == 1
    assert response.items[0].name == "Suyash Gaur"
    assert response.items[0].score == 92.5
    assert response.items[0].award == "Gladiator"


def test_regression_user_with_no_okrs_score_zero(db_session):
    """User with no OKRs -> score 0%."""
    org = Organization(id=uuid.uuid4(), name="Zero Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    batch = Batch(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Zero Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=datetime(2026, 1, 1).date(),
        end_date=datetime(2026, 3, 31).date(),
        meeting_day=MeetingDay.MONDAY,
        status=BatchStatus.ACTIVE,
        is_deleted=False,
    )
    db_session.add_all([org, role, batch])

    user = User(
        id=uuid.uuid4(),
        username="empty_user",
        email="empty@test.com",
        password_hash="h",
        first_name="Empty",
        last_name="User",
        is_deleted=False,
    )
    db_session.add(user)

    mem = OrganizationMember(
        id=uuid.uuid4(),
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
        is_deleted=False,
        is_active=True,
    )
    db_session.add(mem)
    db_session.commit()

    response = get_leaderboard_service(db=db_session, current_user_id=user.id)
    assert len(response.items) == 1
    assert response.items[0].name == "Empty User"
    assert response.items[0].score == 0.0
    assert response.items[0].award == "Bronze"


# =========================================================
# Service & Database Tests
# =========================================================

def override_get_db(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


def test_get_leaderboard_service_user_without_org(db_session):
    user = User(
        id=uuid.uuid4(),
        username="no_org_user",
        email="no_org@example.com",
        password_hash="hash",
        first_name="NoOrg",
        is_deleted=False,
    )
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        get_leaderboard_service(db=db_session, current_user_id=user.id)

    assert exc_info.value.status_code == 404
    assert "Active organization membership not found" in exc_info.value.detail


def test_get_leaderboard_service_success(db_session):
    # Setup Organization & Role
    org = Organization(id=uuid.uuid4(), name="Leaderboard Test Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    db_session.add(org)
    db_session.add(role)

    # Setup Batch
    batch = Batch(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Q1 2026 Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=datetime(2026, 1, 1).date(),
        end_date=datetime(2026, 3, 31).date(),
        meeting_day=MeetingDay.MONDAY,
        status=BatchStatus.ACTIVE,
        is_deleted=False,
    )
    db_session.add(batch)

    # Setup User 1 (Gladiator: 95%)
    user1 = User(id=uuid.uuid4(), username="u1", email="u1@test.com", password_hash="hash", first_name="Alice", last_name="Smith", is_deleted=False)
    db_session.add(user1)
    mem1 = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user1.id, role_id=role.id, is_deleted=False, is_active=True)
    db_session.add(mem1)

    okr1 = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem1.id, objective="Obj 1", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    db_session.add(okr1)
    t1 = TrackerEntry(id=uuid.uuid4(), okr_id=okr1.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=95, is_deleted=False)
    db_session.add(t1)

    # Setup User 2 (Gold: 70%)
    user2 = User(id=uuid.uuid4(), username="u2", email="u2@test.com", password_hash="hash", first_name="Bob", last_name="Jones", is_deleted=False)
    db_session.add(user2)
    mem2 = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user2.id, role_id=role.id, is_deleted=False, is_active=True)
    db_session.add(mem2)

    okr2 = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem2.id, objective="Obj 2", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    db_session.add(okr2)
    t2 = TrackerEntry(id=uuid.uuid4(), okr_id=okr2.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=70, is_deleted=False)
    db_session.add(t2)

    db_session.commit()

    # Test Service for User 2 (Bob)
    response = get_leaderboard_service(db=db_session, current_user_id=user2.id)

    assert isinstance(response, LeaderboardResponse)
    assert len(response.items) == 2

    # Rankings order: Alice #1 (95.0%), Bob #2 (70.0%)
    assert response.items[0].name == "Alice Smith"
    assert response.items[0].rank == 1
    assert response.items[0].award == "Gladiator"

    assert response.items[1].name == "Bob Jones"
    assert response.items[1].rank == 2
    assert response.items[1].award == "Gold"

    # User 2 Rank check
    assert response.my_rank.rank == 2
    assert response.my_rank.score == 70.0
    assert response.my_rank.award == "Gold"

    # Award distribution check
    assert response.award_distribution.gladiator == 1
    assert response.award_distribution.gold == 1
    assert response.award_distribution.platinum == 0
    assert response.award_distribution.bronze == 0


def test_leaderboard_tie_breaking_alphabetical(db_session):
    org = Organization(id=uuid.uuid4(), name="Tie Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    batch = Batch(id=uuid.uuid4(), organization_id=org.id, name="Tie Batch", year=2026, quarter=Quarter.JFM, start_date=datetime(2026, 1, 1).date(), end_date=datetime(2026, 3, 31).date(), meeting_day=MeetingDay.MONDAY, status=BatchStatus.ACTIVE, is_deleted=False)
    db_session.add_all([org, role, batch])

    # User B: Zora (85%)
    user_zora = User(id=uuid.uuid4(), username="zora", email="zora@test.com", password_hash="h", first_name="Zora", last_name="Xavier", is_deleted=False)
    # User A: Aaron (85%)
    user_aaron = User(id=uuid.uuid4(), username="aaron", email="aaron@test.com", password_hash="h", first_name="Aaron", last_name="Adams", is_deleted=False)
    db_session.add_all([user_zora, user_aaron])

    mem_zora = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user_zora.id, role_id=role.id, is_deleted=False, is_active=True)
    mem_aaron = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user_aaron.id, role_id=role.id, is_deleted=False, is_active=True)
    db_session.add_all([mem_zora, mem_aaron])

    okr_z = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem_zora.id, objective="Obj Z", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    okr_a = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem_aaron.id, objective="Obj A", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    db_session.add_all([okr_z, okr_a])

    t_z = TrackerEntry(id=uuid.uuid4(), okr_id=okr_z.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=85, is_deleted=False)
    t_a = TrackerEntry(id=uuid.uuid4(), okr_id=okr_a.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=85, is_deleted=False)
    db_session.add_all([t_z, t_a])
    db_session.commit()

    response = get_leaderboard_service(db=db_session, current_user_id=user_aaron.id)

    # Tie-breaker should put Aaron Adams (#1) before Zora Xavier (#2)
    assert response.items[0].name == "Aaron Adams"
    assert response.items[0].rank == 1
    assert response.items[1].name == "Zora Xavier"
    assert response.items[1].rank == 2


def test_leaderboard_multiple_okrs_per_user_average(db_session):
    org = Organization(id=uuid.uuid4(), name="Multi OKR Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    batch = Batch(id=uuid.uuid4(), organization_id=org.id, name="B", year=2026, quarter=Quarter.JFM, start_date=datetime(2026, 1, 1).date(), end_date=datetime(2026, 3, 31).date(), meeting_day=MeetingDay.MONDAY, status=BatchStatus.ACTIVE, is_deleted=False)
    db_session.add_all([org, role, batch])

    user = User(id=uuid.uuid4(), username="multi_okr_user", email="multi@test.com", password_hash="h", first_name="Multi", last_name="User", is_deleted=False)
    db_session.add(user)

    mem = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user.id, role_id=role.id, is_deleted=False, is_active=True)
    db_session.add(mem)

    # OKR 1: 100%, OKR 2: 80%, OKR 3: 60% => Average = 80% (Platinum)
    okr1 = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem.id, objective="O1", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    okr2 = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem.id, objective="O2", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    okr3 = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem.id, objective="O3", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    db_session.add_all([okr1, okr2, okr3])

    t1 = TrackerEntry(id=uuid.uuid4(), okr_id=okr1.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=100, is_deleted=False)
    t2 = TrackerEntry(id=uuid.uuid4(), okr_id=okr2.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=80, is_deleted=False)
    t3 = TrackerEntry(id=uuid.uuid4(), okr_id=okr3.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=60, is_deleted=False)
    db_session.add_all([t1, t2, t3])
    db_session.commit()

    response = get_leaderboard_service(db=db_session, current_user_id=user.id)

    assert len(response.items) == 1
    assert response.items[0].score == 80.0
    assert response.items[0].award == "Platinum"


def test_leaderboard_ignores_deleted_and_inactive(db_session):
    org = Organization(id=uuid.uuid4(), name="Soft Delete Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    batch = Batch(id=uuid.uuid4(), organization_id=org.id, name="B", year=2026, quarter=Quarter.JFM, start_date=datetime(2026, 1, 1).date(), end_date=datetime(2026, 3, 31).date(), meeting_day=MeetingDay.MONDAY, status=BatchStatus.ACTIVE, is_deleted=False)
    db_session.add_all([org, role, batch])

    # Active User
    active_user = User(id=uuid.uuid4(), username="active_user", email="active@test.com", password_hash="h", first_name="Active", last_name="User", is_deleted=False)
    # Inactive User
    inactive_user = User(id=uuid.uuid4(), username="inactive_user", email="inactive@test.com", password_hash="h", first_name="Inactive", last_name="User", is_deleted=False)
    db_session.add_all([active_user, inactive_user])

    mem_active = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=active_user.id, role_id=role.id, is_deleted=False, is_active=True)
    mem_inactive = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=inactive_user.id, role_id=role.id, is_deleted=False, is_active=False)
    db_session.add_all([mem_active, mem_inactive])

    # Deleted OKR for active user
    deleted_okr = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem_active.id, objective="Deleted Obj", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=True)
    # Active OKR for active user
    valid_okr = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem_active.id, objective="Valid Obj", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    # Active OKR for inactive user (should be excluded as user member is inactive)
    inactive_okr = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=mem_inactive.id, objective="Inactive Obj", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    db_session.add_all([deleted_okr, valid_okr, inactive_okr])

    t1 = TrackerEntry(id=uuid.uuid4(), okr_id=valid_okr.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=90, is_deleted=False)
    t_inactive = TrackerEntry(id=uuid.uuid4(), okr_id=inactive_okr.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=30, is_deleted=False)
    db_session.add_all([t1, t_inactive])
    db_session.commit()

    response = get_leaderboard_service(db=db_session, current_user_id=active_user.id)

    # Only active_user should be listed, score should be 90.0 (ignoring deleted_okr and inactive user OKR)
    assert len(response.items) == 1
    assert response.items[0].name == "Active User"
    assert response.items[0].score == 90.0


def test_leaderboard_multi_tenant_isolation(db_session):
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    orgA = Organization(id=uuid.uuid4(), name="Tenant A", is_deleted=False)
    orgB = Organization(id=uuid.uuid4(), name="Tenant B", is_deleted=False)
    batchA = Batch(id=uuid.uuid4(), organization_id=orgA.id, name="Batch A", year=2026, quarter=Quarter.JFM, start_date=datetime(2026, 1, 1).date(), end_date=datetime(2026, 3, 31).date(), meeting_day=MeetingDay.MONDAY, status=BatchStatus.ACTIVE, is_deleted=False)
    batchB = Batch(id=uuid.uuid4(), organization_id=orgB.id, name="Batch B", year=2026, quarter=Quarter.JFM, start_date=datetime(2026, 1, 1).date(), end_date=datetime(2026, 3, 31).date(), meeting_day=MeetingDay.MONDAY, status=BatchStatus.ACTIVE, is_deleted=False)
    db_session.add_all([role, orgA, orgB, batchA, batchB])

    userA = User(id=uuid.uuid4(), username="userA", email="a@tenant.com", password_hash="h", first_name="User", last_name="A", is_deleted=False)
    userB = User(id=uuid.uuid4(), username="userB", email="b@tenant.com", password_hash="h", first_name="User", last_name="B", is_deleted=False)
    db_session.add_all([userA, userB])

    memA = OrganizationMember(id=uuid.uuid4(), organization_id=orgA.id, user_id=userA.id, role_id=role.id, is_deleted=False, is_active=True)
    memB = OrganizationMember(id=uuid.uuid4(), organization_id=orgB.id, user_id=userB.id, role_id=role.id, is_deleted=False, is_active=True)
    db_session.add_all([memA, memB])

    okrA = OKR(id=uuid.uuid4(), batch_id=batchA.id, assigned_to=memA.id, objective="Obj A", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    okrB = OKR(id=uuid.uuid4(), batch_id=batchB.id, assigned_to=memB.id, objective="Obj B", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
    db_session.add_all([okrA, okrB])

    tA = TrackerEntry(id=uuid.uuid4(), okr_id=okrA.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=90, is_deleted=False)
    tB = TrackerEntry(id=uuid.uuid4(), okr_id=okrB.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=60, is_deleted=False)
    db_session.add_all([tA, tB])
    db_session.commit()

    responseA = get_leaderboard_service(db=db_session, current_user_id=userA.id)
    responseB = get_leaderboard_service(db=db_session, current_user_id=userB.id)

    # Multi-tenant isolation: User A sees only User A, User B sees only User B
    assert len(responseA.items) == 1
    assert responseA.items[0].name == "User A"
    assert responseA.items[0].score == 90.0

    assert len(responseB.items) == 1
    assert responseB.items[0].name == "User B"
    assert responseB.items[0].score == 60.0


def test_award_distribution_all_four_tiers(db_session):
    org = Organization(id=uuid.uuid4(), name="4 Tiers Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    batch = Batch(id=uuid.uuid4(), organization_id=org.id, name="B", year=2026, quarter=Quarter.JFM, start_date=datetime(2026, 1, 1).date(), end_date=datetime(2026, 3, 31).date(), meeting_day=MeetingDay.MONDAY, status=BatchStatus.ACTIVE, is_deleted=False)
    db_session.add_all([org, role, batch])

    users_data = [
        ("u_glad", "Glad", "User", 95),
        ("u_plat", "Plat", "User", 85),
        ("u_gold", "Gold", "User", 65),
        ("u_bro", "Bro", "User", 45),
    ]

    for uname, fname, lname, score in users_data:
        u = User(id=uuid.uuid4(), username=uname, email=f"{uname}@test.com", password_hash="h", first_name=fname, last_name=lname, is_deleted=False)
        db_session.add(u)
        m = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=u.id, role_id=role.id, is_deleted=False, is_active=True)
        db_session.add(m)
        o = OKR(id=uuid.uuid4(), batch_id=batch.id, assigned_to=m.id, objective=f"Obj {fname}", target="100", okr_type="PROFESSIONAL", tracker_enabled=True, is_deleted=False)
        db_session.add(o)
        t = TrackerEntry(id=uuid.uuid4(), okr_id=o.id, week_start=datetime(2026, 1, 1).date(), opportunities_received=100, opportunities_completed=score, is_deleted=False)
        db_session.add(t)

    db_session.commit()

    main_user = db_session.query(User).filter_by(username="u_glad").first()
    response = get_leaderboard_service(db=db_session, current_user_id=main_user.id)

    assert response.award_distribution.gladiator == 1
    assert response.award_distribution.platinum == 1
    assert response.award_distribution.gold == 1
    assert response.award_distribution.bronze == 1


# =========================================================
# API Endpoint Integration Tests
# =========================================================

def test_api_leaderboard_unauthenticated():
    response = client.get("/api/leaderboard/")
    assert response.status_code in [401, 403]


def test_api_leaderboard_authenticated_success(db_session):
    # Create User & Org & Role
    user = User(id=uuid.uuid4(), username="leaderboard_api_user", email="api_user@test.com", password_hash="hash", first_name="API", last_name="Tester", is_deleted=False)
    org = Organization(id=uuid.uuid4(), name="API Test Org", is_deleted=False)
    role = Role(id=uuid.uuid4(), name="EMPLOYEE", is_deleted=False)
    db_session.add(user)
    db_session.add(org)
    db_session.add(role)

    mem = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user.id, role_id=role.id, is_deleted=False, is_active=True)
    db_session.add(mem)
    db_session.commit()

    # Override dependencies
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = client.get("/api/leaderboard/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "my_rank" in data
        assert "award_distribution" in data
    finally:
        app.dependency_overrides.clear()
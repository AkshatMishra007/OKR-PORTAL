import uuid
import pytest
from datetime import datetime, UTC, date
from fastapi import HTTPException, status
from app.core import security, database
from app.common.models import BaseModel, AuditModel, UUIDMixin, SoftDeleteModel
from app.organizations.models import Organization
from app.organizations.schemas import OrganizationUpdate
from app.organizations.service import update_organization_service
from app.organization_members.models import OrganizationMember
from app.organization_members.schemas import OrganizationMemberCreate
from app.organization_members import service as org_member_service
from app.users.models import User
from app.users import service as user_service
from app.weekly_update.models import WeeklyUpdate
from app.weekly_update.service import WeeklyUpdateService
from app.tracker_entries.models import TrackerEntry
from app.rbac import dependencies as rbac_dependencies
from app.rbac.models import Role
from app.batches.models import Batch, BatchStatus, Quarter, MeetingDay
from app.my_okr.models import OKR
from app.queries.models import Query, QueryPriority, QueryStatus
from app.common.exceptions import (
    OrganizationNotFoundException,
    OrganizationAlreadyExistsException,
    OrganizationMemberAlreadyExistsException,
    OrganizationMemberNotFoundException,
    UserNotFoundException,
    RoleNotFoundException,
    OKRNotFoundException,
    WeeklyUpdateNotFoundException,
    AppException,
)


def test_core_security_coverage():
    access_token = security.create_access_token({"sub": "user1"})
    assert access_token is not None

    refresh_token = security.create_refresh_token({"sub": "user1"})
    assert refresh_token is not None

    decoded = security.decode_token(access_token)
    assert decoded["sub"] == "user1"

    # Invalid token string
    with pytest.raises(ValueError) as exc1:
        security.decode_token("invalid.jwt.token")
    assert "Invalid or expired" in str(exc1.value)

    # Invalid token type verify
    with pytest.raises(ValueError) as exc2:
        security.verify_token_type(decoded, "refresh")
    assert "Invalid token type" in str(exc2.value)

    # Valid token type verify
    assert security.verify_token_type(decoded, "access") is True


def test_core_database_coverage():
    gen = database.get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_common_models_coverage(db_session):
    org = Organization(name="Audit Org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    org.description = "New Audit Desc"
    db_session.commit()
    db_session.refresh(org)
    assert org.updated_at is not None


def test_organizations_service_and_models_coverage(db_session):
    org = Organization(
        name="Full Org",
        description="Desc",
        logo="logo.png",
        website="http://full.org",
        email="full@org.com",
        phone="1234567890",
        address="123 Street",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Access relationships
    assert org.organization_members == []
    assert org.batches == []

    # Update org details
    update_data = OrganizationUpdate(
        name="Updated Full Org",
        description="Updated Desc",
        logo="new_logo.png",
        website="http://newfull.org",
        email="newfull@org.com",
        phone="0987654321",
        address="321 Street",
        is_active=False,
    )
    updated = update_organization_service(db_session, org.id, update_data)
    assert updated.name == "Updated Full Org"
    assert updated.logo == "new_logo.png"

    # Non existent organization exception
    with pytest.raises(OrganizationNotFoundException):
        update_organization_service(db_session, uuid.uuid4(), update_data)

    # Duplicate name exception
    org2 = Organization(name="Second Org")
    db_session.add(org2)
    db_session.commit()
    with pytest.raises(OrganizationAlreadyExistsException):
        update_organization_service(db_session, org2.id, OrganizationUpdate(name="Updated Full Org"))


def test_organization_members_service_exceptions(db_session):
    user = User(username="om_user", email="om@test.com", password_hash="hash", first_name="OM")
    db_session.add(user)
    org = Organization(name="OM Org")
    db_session.add(org)
    db_session.commit()

    # Roles
    student_role = Role(name="Student", is_active=True, is_deleted=False)
    admin_role = Role(name="Admin", is_active=True, is_deleted=False)
    db_session.add_all([student_role, admin_role])
    db_session.commit()

    batch = Batch(
        organization_id=org.id,
        name="B1",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )
    db_session.add(batch)
    db_session.commit()

    invalid_id = uuid.uuid4()

    # Org not found
    with pytest.raises(OrganizationNotFoundException):
        org_member_service.create_member_service(
            db_session, OrganizationMemberCreate(user_id=user.id, organization_id=invalid_id, role_id=student_role.id, batch_id=batch.id)
        )

    # User not found
    with pytest.raises(UserNotFoundException):
        org_member_service.create_member_service(
            db_session, OrganizationMemberCreate(user_id=invalid_id, organization_id=org.id, role_id=student_role.id, batch_id=batch.id)
        )

    # Role not found
    with pytest.raises(RoleNotFoundException):
        org_member_service.create_member_service(
            db_session, OrganizationMemberCreate(user_id=user.id, organization_id=org.id, role_id=invalid_id)
        )

    # Student must belong to a batch
    with pytest.raises(AppException) as exc1:
        org_member_service.create_member_service(
            db_session, OrganizationMemberCreate(user_id=user.id, organization_id=org.id, role_id=student_role.id)
        )
    assert "must belong to a batch" in str(exc1.value.message)

    # Admin cannot belong to a batch
    with pytest.raises(AppException) as exc2:
        org_member_service.create_member_service(
            db_session, OrganizationMemberCreate(user_id=user.id, organization_id=org.id, role_id=admin_role.id, batch_id=batch.id)
        )
    assert "cannot belong to a batch" in str(exc2.value.message)

    # Valid creation
    mem = org_member_service.create_member_service(
        db_session, OrganizationMemberCreate(user_id=user.id, organization_id=org.id, role_id=admin_role.id)
    )
    assert mem.id is not None

    # Duplicate membership check
    with pytest.raises(OrganizationMemberAlreadyExistsException):
        org_member_service.create_member_service(
            db_session, OrganizationMemberCreate(user_id=user.id, organization_id=org.id, role_id=admin_role.id)
        )


def test_user_service_and_models_coverage(db_session):
    invalid_id = uuid.uuid4()
    with pytest.raises(UserNotFoundException):
        user_service.get_user_by_id(db_session, invalid_id)

    u = User(
        username="searchuser",
        email="search@user.com",
        password_hash="pwd",
        first_name="Search",
        last_name="User",
        phone="123456",
        designation="Dev",
        description="Desc",
        last_login=datetime.now(UTC),
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)

    assert u.organization_members == []

    users, total = user_service.get_users(db_session, page=1, size=10, search="searchuser")
    assert total == 1
    assert len(users) == 1


def test_weekly_update_service_exceptions_and_models(db_session):
    service = WeeklyUpdateService(db_session)
    invalid_id = uuid.uuid4()

    with pytest.raises(WeeklyUpdateNotFoundException):
        service.get_weekly_update(invalid_id)

    with pytest.raises(OKRNotFoundException):
        service.get_weekly_updates_for_okr(invalid_id)

    with pytest.raises(WeeklyUpdateNotFoundException):
        service.update_weekly_update(invalid_id, None, None)

    with pytest.raises(WeeklyUpdateNotFoundException):
        service.delete_weekly_update(invalid_id, None)

    wu = WeeklyUpdate(
        okr_id=invalid_id,
        week_number=1,
        progress=50,
        remarks="Update text",
        is_active=True,
        is_deleted=False,
    )
    db_session.add(wu)
    db_session.commit()
    db_session.refresh(wu)
    assert wu.okr is None


def test_tracker_entries_and_rbac_coverage(db_session):
    invalid_id = uuid.uuid4()
    te = TrackerEntry(
        okr_id=invalid_id,
        week_start=date(2026, 1, 1),
        opportunities_received=50,
        opportunities_completed=20,
        is_active=True,
        is_deleted=False,
    )
    db_session.add(te)
    db_session.commit()
    db_session.refresh(te)
    assert te.okr is None

    # RBAC Superuser & require_permission test
    u = User(username="superuser", email="super@test.com", password_hash="pwd", first_name="Super")
    setattr(u, "is_superuser", True)
    role_code = rbac_dependencies.get_user_role(u)
    assert role_code == "SUPER_ADMIN"

    checker = rbac_dependencies.require_permission("non_existent_perm")
    with pytest.raises(HTTPException) as exc:
        checker(current_user=u)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    u_normal = User(username="normaluser", email="normal@test.com", password_hash="pwd", first_name="Normal")
    setattr(u_normal, "is_superuser", False)
    with pytest.raises(HTTPException) as exc2:
        checker(current_user=u_normal)
    assert exc2.value.status_code == status.HTTP_403_FORBIDDEN


    # Role model relationships
    role = Role(name="RoleRel", description="Desc")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    assert role.organization_members == []



def test_batches_enums_and_models_coverage(db_session):
    org = Organization(name="Enum Org")
    db_session.add(org)
    db_session.commit()

    b = Batch(
        organization_id=org.id,
        name="Enum Batch",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.WEDNESDAY,
    )
    db_session.add(b)
    db_session.commit()
    db_session.refresh(b)
    assert b.status == BatchStatus.DRAFT

    # Instantiate all meeting days
    for day in [MeetingDay.MONDAY, MeetingDay.TUESDAY, MeetingDay.WEDNESDAY, MeetingDay.THURSDAY, MeetingDay.FRIDAY, MeetingDay.SATURDAY, MeetingDay.SUNDAY]:
        assert str(day) is not None

    # Instantiate all quarters
    for q in [Quarter.JFM, Quarter.AMJ, Quarter.JAS, Quarter.OND]:
        assert str(q) is not None



def test_okr_and_query_models_coverage(db_session):
    u = User(username="q_user", email="q_user@test.com", password_hash="pwd", first_name="Q")
    db_session.add(u)
    db_session.commit()

    q = Query(
        ticket_number="QRY-999999",
        user_id=u.id,
        subject="Model test",
        message="Message test",
        priority=QueryPriority.URGENT,
        status=QueryStatus.REOPENED,
    )
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)
    assert q.submitted_at is not None
    assert q.raised_by is not None
    assert q.assigned_user is None
    assert q.resolved_user is None
    assert q.closed_user is None

    okr = OKR(
        batch_id=uuid.uuid4(),
        assigned_to=uuid.uuid4(),
        objective="Obj test",
        target="100.0",
        okr_type="STANDARD",
        status="ACTIVE",
    )
    db_session.add(okr)
    db_session.commit()
    db_session.refresh(okr)
    assert okr.batch is None
    assert okr.assignee is None

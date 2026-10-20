import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.batches.models import BatchMember, Quarter, MeetingDay
from app.batches.schemas import BatchCreate
from app.batches.service import BatchService
from app.common.exceptions import UserNotFoundException
from app.core.database import get_db
from app.main import app
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


def test_create_batch_without_users_and_admins(db_session):
    org = Organization(name="Org No Members")
    admin_role = Role(name="ORG_ADMIN")
    db_session.add_all([org, admin_role])
    db_session.commit()

    creator = User(username="creator_no_mem", email="c_nomem@test.com", password_hash="hash", first_name="Creator")
    db_session.add(creator)
    db_session.commit()

    creator_member = OrganizationMember(
        organization_id=org.id,
        user_id=creator.id,
        role_id=admin_role.id,
        is_active=True,
        is_deleted=False,
    )
    db_session.add(creator_member)
    db_session.commit()

    batch_payload = BatchCreate(
        organization_id=org.id,
        name="Empty Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )

    service = BatchService(db_session)
    batch = service.create_batch(batch_payload, creator)

    assert batch.id is not None
    assert batch.users == []
    assert batch.admins == []

    members = db_session.query(BatchMember).filter_by(batch_id=batch.id).all()
    assert len(members) == 0


def test_create_batch_with_multiple_users(db_session):
    org = Organization(name="Org Multi Users")
    emp_role = Role(name="Employee")
    db_session.add_all([org, emp_role])
    db_session.commit()

    u1 = User(username="mu1", email="mu1@test.com", password_hash="h", first_name="Multi1")
    u2 = User(username="mu2", email="mu2@test.com", password_hash="h", first_name="Multi2")
    db_session.add_all([u1, u2])
    db_session.commit()

    m1 = OrganizationMember(organization_id=org.id, user_id=u1.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    m2 = OrganizationMember(organization_id=org.id, user_id=u2.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    db_session.add_all([m1, m2])
    db_session.commit()

    batch_payload = BatchCreate(
        organization_id=org.id,
        name="Multi Users Batch",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.TUESDAY,
        batch_users=[u1.id, u2.id],
    )

    service = BatchService(db_session)
    batch = service.create_batch(batch_payload, None)

    assert len(batch.users) == 2
    user_ids = {u.id for u in batch.users}
    assert u1.id in user_ids
    assert u2.id in user_ids
    assert len(batch.admins) == 0


def test_create_batch_with_multiple_admins(db_session):
    org = Organization(name="Org Multi Admins")
    admin_role = Role(name="Batch Admin")
    db_session.add_all([org, admin_role])
    db_session.commit()

    a1 = User(username="ma1", email="ma1@test.com", password_hash="h", first_name="Admin1")
    a2 = User(username="ma2", email="ma2@test.com", password_hash="h", first_name="Admin2")
    db_session.add_all([a1, a2])
    db_session.commit()

    m1 = OrganizationMember(organization_id=org.id, user_id=a1.id, role_id=admin_role.id, is_active=True, is_deleted=False)
    m2 = OrganizationMember(organization_id=org.id, user_id=a2.id, role_id=admin_role.id, is_active=True, is_deleted=False)
    db_session.add_all([m1, m2])
    db_session.commit()

    batch_payload = BatchCreate(
        organization_id=org.id,
        name="Multi Admins Batch",
        year=2026,
        quarter=Quarter.JAS,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        meeting_day=MeetingDay.WEDNESDAY,
        batch_admins=[a1.id, a2.id],
    )

    service = BatchService(db_session)
    batch = service.create_batch(batch_payload, None)

    assert len(batch.admins) == 2
    admin_ids = {a.id for a in batch.admins}
    assert a1.id in admin_ids
    assert a2.id in admin_ids
    assert len(batch.users) == 0


def test_create_batch_with_batch_users_and_admins(db_session):
    org = Organization(name="Test Org Batch")
    db_session.add(org)

    emp_role = Role(name="Employee")
    admin_role = Role(name="Batch Admin")
    org_admin_role = Role(name="ORG_ADMIN")
    db_session.add_all([emp_role, admin_role, org_admin_role])
    db_session.commit()

    user1 = User(username="usr1", email="usr1@test.com", password_hash="hash", first_name="User1")
    user2 = User(username="usr2", email="usr2@test.com", password_hash="hash", first_name="User2")
    admin_usr = User(username="usr3", email="usr3@test.com", password_hash="hash", first_name="User3")
    creator = User(username="creator", email="creator@test.com", password_hash="hash", first_name="Creator")
    db_session.add_all([user1, user2, admin_usr, creator])
    db_session.commit()

    m_creator = OrganizationMember(organization_id=org.id, user_id=creator.id, role_id=org_admin_role.id, is_active=True, is_deleted=False)
    m1 = OrganizationMember(organization_id=org.id, user_id=user1.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    m2 = OrganizationMember(organization_id=org.id, user_id=user2.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    m3 = OrganizationMember(organization_id=org.id, user_id=admin_usr.id, role_id=admin_role.id, is_active=True, is_deleted=False)
    db_session.add_all([m_creator, m1, m2, m3])
    db_session.commit()

    batch_payload = BatchCreate(
        organization_id=org.id,
        name="Test Batch 2026",
        year=2026,
        quarter=Quarter.JAS,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user1.id, user2.id],
        batch_admins=[admin_usr.id],
    )

    service = BatchService(db_session)
    batch = service.create_batch(batch_payload, creator)

    assert batch.id is not None
    assert len(batch.users) == 2
    assert len(batch.admins) == 1

    # Query newly created BatchMember records for this batch
    members = db_session.query(BatchMember).filter_by(batch_id=batch.id).all()
    assert len(members) == 3

    member_user_ids = {m.user_id for m in members}
    assert user1.id in member_user_ids
    assert user2.id in member_user_ids
    assert admin_usr.id in member_user_ids

    # Fetch batch afterward and verify users and admins are populated
    fetched_detail = service.get_batch(batch.id, creator)
    fetched_data = fetched_detail["data"]
    assert len(fetched_data["users"]) == 2
    assert len(fetched_data["admins"]) == 1


def test_create_batch_duplicate_user_ids_handled(db_session):
    org = Organization(name="Org Dup IDs")
    emp_role = Role(name="Employee")
    db_session.add_all([org, emp_role])
    db_session.commit()

    u1 = User(username="dup1", email="dup1@test.com", password_hash="h", first_name="Dup1")
    db_session.add(u1)
    db_session.commit()

    m1 = OrganizationMember(organization_id=org.id, user_id=u1.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    db_session.add(m1)
    db_session.commit()

    batch_payload = BatchCreate(
        organization_id=org.id,
        name="Dup Users Batch",
        year=2026,
        quarter=Quarter.OND,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 31),
        meeting_day=MeetingDay.FRIDAY,
        batch_users=[u1.id, u1.id],
    )

    service = BatchService(db_session)
    batch = service.create_batch(batch_payload, None)

    assert len(batch.users) == 1
    members = db_session.query(BatchMember).filter_by(batch_id=batch.id).all()
    assert len(members) == 1


def test_create_batch_invalid_user_id_raises_exception(db_session):
    org = Organization(name="Org Invalid User")
    emp_role = Role(name="Employee")
    db_session.add_all([org, emp_role])
    db_session.commit()

    invalid_uuid = uuid.uuid4()
    batch_payload = BatchCreate(
        organization_id=org.id,
        name="Invalid User Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[invalid_uuid],
    )

    service = BatchService(db_session)
    with pytest.raises(UserNotFoundException):
        service.create_batch(batch_payload, None)


def test_create_batch_api_endpoint_returns_populated_users_and_admins(db_session):
    org = Organization(name="API Test Org")
    emp_role = Role(name="Employee")
    admin_role = Role(name="Batch Admin")
    org_admin_role = Role(name="ORG_ADMIN")
    db_session.add_all([org, emp_role, admin_role, org_admin_role])
    db_session.commit()

    u1 = User(username="api_u1", email="api_u1@test.com", password_hash="h", first_name="APIUser1")
    u2 = User(username="api_u2", email="api_u2@test.com", password_hash="h", first_name="APIUser2")
    a1 = User(username="api_a1", email="api_a1@test.com", password_hash="h", first_name="APIAdmin1")
    db_session.add_all([u1, u2, a1])
    db_session.commit()

    m1 = OrganizationMember(organization_id=org.id, user_id=u1.id, role_id=org_admin_role.id, is_active=True, is_deleted=False)
    m2 = OrganizationMember(organization_id=org.id, user_id=u2.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    ma = OrganizationMember(organization_id=org.id, user_id=a1.id, role_id=admin_role.id, is_active=True, is_deleted=False)
    db_session.add_all([m1, m2, ma])
    db_session.commit()

    client = TestClient(app)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_current_user():
        return u1

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        response = client.post(
            "/api/batches/",
            headers={"X-Organization-ID": str(org.id)},
            json={
                "organization_id": str(org.id),
                "name": "API Batch 2026",
                "year": 2026,
                "quarter": "JAS",
                "start_date": "2026-07-01",
                "end_date": "2026-09-30",
                "meeting_day": "MONDAY",
                "batch_users": [str(u1.id), str(u2.id)],
                "batch_admins": [str(a1.id)],
            },
        )

        assert response.status_code == 201, response.text
        res_data = response.json()

        assert res_data["name"] == "API Batch 2026"
        assert len(res_data["users"]) == 2
        assert len(res_data["admins"]) == 1

        user_emails = {u["email"] for u in res_data["users"]}
        assert "api_u1@test.com" in user_emails
        assert "api_u2@test.com" in user_emails

        admin_emails = {a["email"] for a in res_data["admins"]}
        assert "api_a1@test.com" in admin_emails
    finally:
        app.dependency_overrides.clear()

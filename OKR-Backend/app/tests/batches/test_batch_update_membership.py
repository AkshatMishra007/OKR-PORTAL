import uuid
from datetime import date
import pytest

from app.batches.models import Batch, BatchMember, Quarter, MeetingDay, BatchStatus
from app.batches.schemas import BatchCreate, BatchUpdate
from app.batches.service import BatchService
from app.common.exceptions import (
    AppException,
    BatchNotFoundException,
    UserNotFoundException,
)
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


@pytest.fixture
def setup_batch_data(db_session):
    org = Organization(name="Org for Batch Update Test")
    db_session.add(org)

    emp_role = Role(name="Employee")
    admin_role = Role(name="Batch Admin")
    org_admin_role = Role(name="ORG_ADMIN")
    db_session.add_all([emp_role, admin_role, org_admin_role])
    db_session.commit()

    u1 = User(username="emp1", email="emp1@test.com", password_hash="pwd", first_name="Employee", last_name="One")
    u2 = User(username="emp2", email="emp2@test.com", password_hash="pwd", first_name="Employee", last_name="Two")
    u3 = User(username="adm1", email="adm1@test.com", password_hash="pwd", first_name="Admin", last_name="One")
    u4 = User(username="adm2", email="adm2@test.com", password_hash="pwd", first_name="Admin", last_name="Two")
    creator = User(username="creator_u", email="creator@test.com", password_hash="pwd", first_name="Creator")
    db_session.add_all([u1, u2, u3, u4, creator])
    db_session.commit()

    mem_creator = OrganizationMember(organization_id=org.id, user_id=creator.id, role_id=org_admin_role.id, is_active=True, is_deleted=False)
    mem_u1 = OrganizationMember(organization_id=org.id, user_id=u1.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    mem_u2 = OrganizationMember(organization_id=org.id, user_id=u2.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    mem_u3 = OrganizationMember(organization_id=org.id, user_id=u3.id, role_id=admin_role.id, is_active=True, is_deleted=False)
    mem_u4 = OrganizationMember(organization_id=org.id, user_id=u4.id, role_id=admin_role.id, is_active=True, is_deleted=False)
    db_session.add_all([mem_creator, mem_u1, mem_u2, mem_u3, mem_u4])
    db_session.commit()

    service = BatchService(db_session)
    batch_payload = BatchCreate(
        organization_id=org.id,
        name="Batch 2026 Q1",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[u1.id],
        batch_admins=[u3.id],
    )
    batch = service.create_batch(batch_payload, creator)

    return {
        "org": org,
        "emp_role": emp_role,
        "admin_role": admin_role,
        "u1": u1,
        "u2": u2,
        "u3": u3,
        "u4": u4,
        "creator": creator,
        "batch": batch,
        "service": service,
    }


def test_get_batch_members(setup_batch_data, db_session):
    d = setup_batch_data
    service = d["service"]

    res = service.get_batch(d["batch"].id, d["creator"])
    assert "data" in res
    users = res["data"]["users"]
    admins = res["data"]["admins"]

    assert len(users) == 1
    assert users[0].id == d["u1"].id
    assert users[0].name == "Employee One"

    assert len(admins) == 1
    assert admins[0].id == d["u3"].id
    assert admins[0].name == "Admin One"


def test_update_batch_add_and_remove_members(setup_batch_data, db_session):
    d = setup_batch_data
    service = d["service"]
    batch = d["batch"]

    # Add u2 to users, replace u3 with u4 in admins
    update_payload = BatchUpdate(
        batch_users=[d["u1"].id, d["u2"].id],
        batch_admins=[d["u4"].id],
    )
    updated_batch = service.update_batch(batch.id, update_payload, d["creator"])
    assert updated_batch.id == batch.id

    res = service.get_batch(batch.id, d["creator"])
    user_ids = {u.id for u in res["data"]["users"]}
    admin_ids = {a.id for a in res["data"]["admins"]}

    assert user_ids == {d["u1"].id, d["u2"].id}
    assert admin_ids == {d["u4"].id}

    # Verify soft delete for u3 in BatchMember
    soft_deleted_member = db_session.query(BatchMember).filter_by(
        batch_id=batch.id, user_id=d["u3"].id, role_id=d["admin_role"].id
    ).first()
    assert soft_deleted_member.is_deleted is True
    assert soft_deleted_member.is_active is False

    # Verify u3's OrganizationMember is untouched
    org_member = db_session.query(OrganizationMember).filter_by(
        organization_id=d["org"].id, user_id=d["u3"].id
    ).first()
    assert org_member.is_deleted is False
    assert org_member.is_active is True


def test_update_batch_none_preserves_and_empty_list_clears(setup_batch_data, db_session):
    d = setup_batch_data
    service = d["service"]
    batch = d["batch"]

    # batch_users is None (preserve u1), batch_admins is [] (clear u3)
    update_payload = BatchUpdate(
        batch_users=None,
        batch_admins=[],
    )
    service.update_batch(batch.id, update_payload, d["creator"])

    res = service.get_batch(batch.id, d["creator"])
    assert len(res["data"]["users"]) == 1
    assert res["data"]["users"][0].id == d["u1"].id
    assert len(res["data"]["admins"]) == 0


def test_rule1_user_cannot_be_both_roles(setup_batch_data):
    d = setup_batch_data
    service = d["service"]
    batch = d["batch"]

    # Dual role in same payload
    update_payload = BatchUpdate(
        batch_users=[d["u2"].id],
        batch_admins=[d["u2"].id],
    )
    with pytest.raises(AppException) as exc_info:
        service.update_batch(batch.id, update_payload, d["creator"])
    assert "User cannot be both Employee and Batch Admin in the same batch." in str(exc_info.value)

    # u3 is currently admin, try adding u3 as user while preserving admins (None)
    update_payload_2 = BatchUpdate(
        batch_users=[d["u3"].id],
        batch_admins=None,
    )
    with pytest.raises(AppException) as exc_info2:
        service.update_batch(batch.id, update_payload_2, d["creator"])
    assert "User cannot be both Employee and Batch Admin in the same batch." in str(exc_info2.value)


def test_rule2_employee_cannot_belong_to_multiple_batches(setup_batch_data, db_session):
    d = setup_batch_data
    service = d["service"]

    # Create Batch 2
    batch2_payload = BatchCreate(
        organization_id=d["org"].id,
        name="Batch 2026 Q2",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[],
        batch_admins=[],
    )
    batch2 = service.create_batch(batch2_payload, d["creator"])

    # Try assigning u1 (who is employee in Batch 1) as employee in Batch 2
    update_payload = BatchUpdate(
        batch_users=[d["u1"].id],
    )
    with pytest.raises(AppException) as exc_info:
        service.update_batch(batch2.id, update_payload, d["creator"])
    assert "Employee is already assigned to another batch." in str(exc_info.value)


def test_rule3_invalid_user_uuid(setup_batch_data):
    d = setup_batch_data
    service = d["service"]
    batch = d["batch"]
    fake_id = uuid.uuid4()

    update_payload = BatchUpdate(
        batch_users=[fake_id],
    )
    with pytest.raises(UserNotFoundException) as exc_info:
        service.update_batch(batch.id, update_payload, d["creator"])
    assert f"User not found: {fake_id}" in str(exc_info.value)

import uuid
from datetime import date
import pytest

from app.batches.models import Quarter, MeetingDay, Batch, BatchMember
from app.batches.schemas import BatchCreate
from app.batches.service import BatchService
from app.common.exceptions import AppException
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


def setup_org_and_roles(db_session):
    """Helper fixture to create Organization and basic RBAC roles."""
    org = Organization(name=f"Test Org Logic Fix {uuid.uuid4().hex[:6]}")
    emp_role = Role(name="Employee")
    admin_role = Role(name="Batch Admin")
    org_admin_role = Role(name="ORG_ADMIN")
    db_session.add_all([org, emp_role, admin_role, org_admin_role])
    db_session.commit()
    return org, emp_role, admin_role, org_admin_role


def test_case_1_employee_has_no_batch(db_session):
    """
    Case 1 — Employee has no batch (no BatchMember record).
    Expected: Batch creation succeeds.
    """
    org, emp_role, admin_role, org_admin_role = setup_org_and_roles(db_session)

    user = User(username="no_batch_user", email="nobatch@test.com", password_hash="hash", first_name="NoBatch")
    creator = User(username="creator1", email="creator1@test.com", password_hash="hash", first_name="Creator")
    db_session.add_all([user, creator])
    db_session.commit()

    # User and creator are members of the org
    unassigned_member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=emp_role.id,
        is_active=True,
        is_deleted=False,
    )
    creator_member = OrganizationMember(
        organization_id=org.id,
        user_id=creator.id,
        role_id=org_admin_role.id,
        is_active=True,
        is_deleted=False,
    )
    db_session.add_all([unassigned_member, creator_member])
    db_session.commit()

    payload = BatchCreate(
        organization_id=org.id,
        name="Case 1 Batch",
        year=2026,
        quarter=Quarter.JAS,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user.id],
        batch_admins=[],
    )

    service = BatchService(db_session)
    batch = service.create_batch(payload, creator)

    assert batch.id is not None
    # Verify new batch membership was created in BatchMember
    new_member = (
        db_session.query(BatchMember)
        .filter_by(user_id=user.id, batch_id=batch.id)
        .first()
    )
    assert new_member is not None
    assert new_member.role_id == emp_role.id


def test_case_2_employee_already_belongs_to_active_batch(db_session):
    """
    Case 2 — Employee already belongs to an active batch in BatchMember.
    Expected: Rejected with 'Employee is already assigned to another batch.'
    """
    org, emp_role, admin_role, org_admin_role = setup_org_and_roles(db_session)

    existing_batch = Batch(
        organization_id=org.id,
        name="Existing Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )
    db_session.add(existing_batch)
    db_session.commit()

    user = User(username="assigned_user", email="assigned@test.com", password_hash="hash", first_name="Assigned")
    creator = User(username="creator2", email="creator2@test.com", password_hash="hash", first_name="Creator")
    db_session.add_all([user, creator])
    db_session.commit()

    org_member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=emp_role.id,
        is_active=True,
        is_deleted=False,
    )
    creator_member = OrganizationMember(
        organization_id=org.id,
        user_id=creator.id,
        role_id=org_admin_role.id,
        is_active=True,
        is_deleted=False,
    )
    # User already assigned to existing_batch in BatchMember
    assigned_batch_member = BatchMember(
        batch_id=existing_batch.id,
        user_id=user.id,
        role_id=emp_role.id,
        is_active=True,
        is_deleted=False,
    )
    db_session.add_all([org_member, creator_member, assigned_batch_member])
    db_session.commit()

    payload = BatchCreate(
        organization_id=org.id,
        name="Case 2 Batch",
        year=2026,
        quarter=Quarter.JAS,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user.id],
        batch_admins=[],
    )

    service = BatchService(db_session)
    with pytest.raises(AppException) as exc_info:
        service.create_batch(payload, creator)

    assert "Employee is already assigned to another batch." in str(exc_info.value)


def test_case_3_employee_has_inactive_or_soft_deleted_membership(db_session):
    """
    Case 3 — Employee has soft-deleted or inactive batch membership (is_active = False or is_deleted = True).
    Expected: Batch creation succeeds.
    """
    org, emp_role, admin_role, org_admin_role = setup_org_and_roles(db_session)

    old_batch = Batch(
        organization_id=org.id,
        name="Old Batch",
        year=2025,
        quarter=Quarter.JFM,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )
    db_session.add(old_batch)
    db_session.commit()

    user_inactive = User(username="inactive_user", email="inactive@test.com", password_hash="hash", first_name="Inactive")
    user_deleted = User(username="deleted_user", email="deleted@test.com", password_hash="hash", first_name="Deleted")
    creator = User(username="creator3", email="creator3@test.com", password_hash="hash", first_name="Creator")
    db_session.add_all([user_inactive, user_deleted, creator])
    db_session.commit()

    mem_inactive = OrganizationMember(organization_id=org.id, user_id=user_inactive.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    mem_deleted = OrganizationMember(organization_id=org.id, user_id=user_deleted.id, role_id=emp_role.id, is_active=True, is_deleted=False)
    creator_member = OrganizationMember(organization_id=org.id, user_id=creator.id, role_id=org_admin_role.id, is_active=True, is_deleted=False)

    # BatchMember with is_active = False
    inactive_bm = BatchMember(
        batch_id=old_batch.id,
        user_id=user_inactive.id,
        role_id=emp_role.id,
        is_active=False,
        is_deleted=False,
    )
    # BatchMember with is_deleted = True
    deleted_bm = BatchMember(
        batch_id=old_batch.id,
        user_id=user_deleted.id,
        role_id=emp_role.id,
        is_active=True,
        is_deleted=True,
    )
    db_session.add_all([mem_inactive, mem_deleted, creator_member, inactive_bm, deleted_bm])
    db_session.commit()

    payload = BatchCreate(
        organization_id=org.id,
        name="Case 3 Batch",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user_inactive.id, user_deleted.id],
        batch_admins=[],
    )

    service = BatchService(db_session)
    batch = service.create_batch(payload, creator)

    assert batch.id is not None


def test_case_4_multiple_unassigned_employees(db_session):
    """
    Case 4 — Multiple employees without active batch assignments.
    Reproducing request payload pattern with four employee UUIDs.
    Expected: Batch creation succeeds atomically.
    """
    org, emp_role, admin_role, org_admin_role = setup_org_and_roles(db_session)

    # 4 Employees with specific reproduction IDs or new user records
    emp1_id = uuid.UUID("08cc7792-6aea-4111-83f6-8a7fa7942452")
    emp2_id = uuid.UUID("4cdb451c-dd0f-4361-ba00-368a36831726")
    emp3_id = uuid.UUID("ed78d135-7ec5-4b26-93f6-03d997576892")
    emp4_id = uuid.UUID("1fb91f92-7eb7-4353-9b48-3fbd22d3c633")
    admin_id = uuid.UUID("7e840bca-c87a-4022-85bb-585bb94562b7")

    u1 = User(id=emp1_id, username="emp1", email="emp1@test.com", password_hash="hash", first_name="Emp1")
    u2 = User(id=emp2_id, username="emp2", email="emp2@test.com", password_hash="hash", first_name="Emp2")
    u3 = User(id=emp3_id, username="emp3", email="emp3@test.com", password_hash="hash", first_name="Emp3")
    u4 = User(id=emp4_id, username="emp4", email="emp4@test.com", password_hash="hash", first_name="Emp4")
    admin_u = User(id=admin_id, username="admin_u", email="admin_u@test.com", password_hash="hash", first_name="Admin")
    creator = User(username="creator4", email="creator4@test.com", password_hash="hash", first_name="Creator")
    db_session.add_all([u1, u2, u3, u4, admin_u, creator])
    db_session.commit()

    # Add all users and admin to org
    for u in [u1, u2, u3, u4]:
        db_session.add(
            OrganizationMember(
                organization_id=org.id,
                user_id=u.id,
                role_id=emp_role.id,
                is_active=True,
                is_deleted=False,
            )
        )
    db_session.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=admin_u.id,
            role_id=admin_role.id,
            is_active=True,
            is_deleted=False,
        )
    )
    db_session.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=creator.id,
            role_id=org_admin_role.id,
            is_active=True,
            is_deleted=False,
        )
    )
    db_session.commit()

    payload = BatchCreate(
        organization_id=org.id,
        name="hr",
        year=2026,
        quarter=Quarter.JAS,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[emp1_id, emp2_id, emp3_id, emp4_id],
        batch_admins=[admin_id],
    )

    service = BatchService(db_session)
    batch = service.create_batch(payload, creator)

    assert batch.id is not None
    assert batch.name == "hr"

    members = db_session.query(BatchMember).filter_by(batch_id=batch.id).all()
    assert len(members) == 5  # 4 employees + 1 admin


def test_case_5_transaction_rollback_on_assigned_employee(db_session):
    """
    Case 5 — Transaction rollback.
    If one employee in batch_users is already assigned to another active batch,
    the entire transaction is rolled back and no batch or partial assignments exist.
    """
    org, emp_role, admin_role, org_admin_role = setup_org_and_roles(db_session)

    existing_batch = Batch(
        organization_id=org.id,
        name="Existing Batch 5",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )
    db_session.add(existing_batch)
    db_session.commit()

    u_free = User(username="u_free", email="ufree@test.com", password_hash="hash", first_name="Free")
    u_busy = User(username="u_busy", email="ubusy@test.com", password_hash="hash", first_name="Busy")
    creator = User(username="creator5", email="creator5@test.com", password_hash="hash", first_name="Creator")
    db_session.add_all([u_free, u_busy, creator])
    db_session.commit()

    # Add to org
    db_session.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=u_free.id,
            role_id=emp_role.id,
            is_active=True,
            is_deleted=False,
        )
    )
    db_session.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=u_busy.id,
            role_id=emp_role.id,
            is_active=True,
            is_deleted=False,
        )
    )
    db_session.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=creator.id,
            role_id=org_admin_role.id,
            is_active=True,
            is_deleted=False,
        )
    )
    # u_busy is assigned to existing_batch in BatchMember
    db_session.add(
        BatchMember(
            batch_id=existing_batch.id,
            user_id=u_busy.id,
            role_id=emp_role.id,
            is_active=True,
            is_deleted=False,
        )
    )
    db_session.commit()

    payload = BatchCreate(
        organization_id=org.id,
        name="Failed Batch",
        year=2026,
        quarter=Quarter.OND,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 31),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[u_free.id, u_busy.id],
        batch_admins=[],
    )

    service = BatchService(db_session)
    with pytest.raises(AppException) as exc_info:
        service.create_batch(payload, creator)

    assert "Employee is already assigned to another batch." in str(exc_info.value)

    # Verify 'Failed Batch' was not saved in DB
    failed_batch = db_session.query(Batch).filter_by(name="Failed Batch").first()
    assert failed_batch is None

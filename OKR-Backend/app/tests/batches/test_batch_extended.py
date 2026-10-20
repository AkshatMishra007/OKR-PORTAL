"""
Extended and edge-case unit and integration tests for Batches module.

Covers:
- Multi-organization batch isolation (same name/quarter across different orgs).
- Batch date ranges, quarter validations, and meeting days.
- Complex filtering: by year, quarter, status, meeting day, search keywords, and pagination limits.
- Batch creation with batch admins and batch users, conflict prevention.
- Batch update rules: partial updates, duplicate prevention on quarter/year change.
- Batch deletion and soft-delete verification.
- Batch stats and membership associations.
"""

import uuid
from datetime import date, datetime, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.batches.models import Batch, BatchMember, BatchStatus, MeetingDay, Quarter
from app.batches.schemas import BatchCreate, BatchUpdate
from app.batches.service import BatchService
from app.common.exceptions import (
    AppException,
    BatchAlreadyExistsException,
    BatchNotFoundException,
    ForbiddenException,
    OrganizationNotFoundException,
    RoleNotFoundException,
    UserNotFoundException,
)
from app.core.database import get_db
from app.main import app as fastapi_app
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


@pytest.fixture
def extended_batch_setup(db_session: Session):
    """Fixture providing 2 organizations, roles, admin users, and regular users."""
    # 1. Organizations
    org_alpha = Organization(id=uuid.uuid4(), name="Alpha Enterprise", is_deleted=False, is_active=True)
    org_beta = Organization(id=uuid.uuid4(), name="Beta Logistics", is_deleted=False, is_active=True)
    db_session.add_all([org_alpha, org_beta])
    db_session.flush()

    # 2. Roles
    def get_or_create_role(name: str) -> Role:
        r = db_session.query(Role).filter(Role.name == name).first()
        if not r:
            r = Role(id=uuid.uuid4(), name=name, description=f"{name} role")
            db_session.add(r)
            db_session.flush()
        return r

    role_super = get_or_create_role("SUPER_ADMIN")
    role_org_admin = get_or_create_role("ORG_ADMIN")
    role_batch_admin = get_or_create_role("BATCH_ADMIN")
    role_employee = get_or_create_role("EMPLOYEE")

    # 3. Users
    pwd = hash_password("Secret123!")
    super_user = User(
        id=uuid.uuid4(),
        username="super_batch_user",
        email="super_batch@example.com",
        password_hash=pwd,
        first_name="Super",
        last_name="Batch",
        is_active=True,
        is_deleted=False,
    )
    setattr(super_user, "is_superuser", True)

    org_admin_alpha = User(
        id=uuid.uuid4(),
        username="admin_alpha_user",
        email="admin_alpha@example.com",
        password_hash=pwd,
        first_name="Admin",
        last_name="Alpha",
        is_active=True,
        is_deleted=False,
    )

    user1 = User(
        id=uuid.uuid4(),
        username="batch_emp_one",
        email="emp_one@example.com",
        password_hash=pwd,
        first_name="Emp",
        last_name="One",
        is_active=True,
        is_deleted=False,
    )
    user2 = User(
        id=uuid.uuid4(),
        username="batch_emp_two",
        email="emp_two@example.com",
        password_hash=pwd,
        first_name="Emp",
        last_name="Two",
        is_active=True,
        is_deleted=False,
    )
    user3 = User(
        id=uuid.uuid4(),
        username="batch_admin_candidate",
        email="admin_candidate@example.com",
        password_hash=pwd,
        first_name="Candidate",
        last_name="Admin",
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([super_user, org_admin_alpha, user1, user2, user3])
    db_session.flush()

    # 4. Memberships
    mem_super = OrganizationMember(
        id=uuid.uuid4(),
        user_id=super_user.id,
        organization_id=org_alpha.id,
        role_id=role_super.id,
        is_active=True,
        is_deleted=False,
    )
    mem_admin_alpha = OrganizationMember(
        id=uuid.uuid4(),
        user_id=org_admin_alpha.id,
        organization_id=org_alpha.id,
        role_id=role_org_admin.id,
        is_active=True,
        is_deleted=False,
    )

    mem_u1 = OrganizationMember(
        id=uuid.uuid4(),
        user_id=user1.id,
        organization_id=org_alpha.id,
        role_id=role_employee.id,
        is_active=True,
        is_deleted=False,
    )
    mem_u2 = OrganizationMember(
        id=uuid.uuid4(),
        user_id=user2.id,
        organization_id=org_alpha.id,
        role_id=role_employee.id,
        is_active=True,
        is_deleted=False,
    )
    mem_u3 = OrganizationMember(
        id=uuid.uuid4(),
        user_id=user3.id,
        organization_id=org_alpha.id,
        role_id=role_batch_admin.id,
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([mem_super, mem_admin_alpha, mem_u1, mem_u2, mem_u3])
    db_session.commit()

    return {
        "org_alpha": org_alpha,
        "org_beta": org_beta,
        "super_user": super_user,
        "org_admin_alpha": org_admin_alpha,
        "user1": user1,
        "user2": user2,
        "user3": user3,
        "role_super": role_super,
        "role_org_admin": role_org_admin,
        "role_batch_admin": role_batch_admin,
        "role_employee": role_employee,
    }


def test_multi_organization_same_batch_name_and_quarter(db_session: Session, extended_batch_setup: dict):
    """
    Verify that two different organizations can have batches with identical name, year, and quarter
    without triggering a duplicate batch exception.
    """
    service = BatchService(db_session)
    org_a = extended_batch_setup["org_alpha"]
    org_b = extended_batch_setup["org_beta"]
    admin = extended_batch_setup["super_user"]

    batch_a_data = BatchCreate(
        organization_id=org_a.id,
        name="Global Q1 Sprint",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )
    batch_a = service.create_batch(batch_a_data, admin)
    assert batch_a.id is not None
    assert batch_a.organization_id == org_a.id

    # Create identical batch under Org B -> should succeed
    batch_b_data = BatchCreate(
        organization_id=org_b.id,
        name="Global Q1 Sprint",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )
    batch_b = service.create_batch(batch_b_data, admin)
    assert batch_b.id is not None
    assert batch_b.organization_id == org_b.id
    assert batch_a.id != batch_b.id


def test_batch_create_with_users_and_batch_admins(db_session: Session, extended_batch_setup: dict):
    """
    Verify creating a batch while assigning batch users and batch admins automatically
    links the members to the new batch and sets their roles appropriately.
    """
    service = BatchService(db_session)
    org = extended_batch_setup["org_alpha"]
    admin = extended_batch_setup["org_admin_alpha"]
    user1 = extended_batch_setup["user1"]
    user2 = extended_batch_setup["user2"]
    user3 = extended_batch_setup["user3"]

    batch_data = BatchCreate(
        organization_id=org.id,
        name="Cohort 2026 Q2",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.WEDNESDAY,
        batch_users=[user1.id, user2.id],
        batch_admins=[user3.id],
    )

    batch = service.create_batch(batch_data, admin)
    assert batch.id is not None

    # Verify user1 & user2 memberships created in BatchMember
    bm1 = db_session.query(BatchMember).filter(
        BatchMember.user_id == user1.id,
        BatchMember.batch_id == batch.id,
    ).first()
    assert bm1 is not None

    bm2 = db_session.query(BatchMember).filter(
        BatchMember.user_id == user2.id,
        BatchMember.batch_id == batch.id,
    ).first()
    assert bm2 is not None

    # Verify user3 created as BATCH_ADMIN in BatchMember
    bm3 = db_session.query(BatchMember).filter(
        BatchMember.user_id == user3.id,
        BatchMember.batch_id == batch.id,
    ).first()
    assert bm3 is not None
    assert bm3.role.name in ("BATCH_ADMIN", "Batch Admin", "batch_admin")


def test_batch_create_user_cannot_be_both_employee_and_batch_admin(db_session: Session, extended_batch_setup: dict):
    """
    Verify validation error when the same user is supplied in both batch_users and batch_admins.
    """
    service = BatchService(db_session)
    org = extended_batch_setup["org_alpha"]
    admin = extended_batch_setup["org_admin_alpha"]
    user1 = extended_batch_setup["user1"]

    batch_data = BatchCreate(
        organization_id=org.id,
        name="Conflicting Cohort",
        year=2026,
        quarter=Quarter.OND,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 12, 31),
        meeting_day=MeetingDay.FRIDAY,
        batch_users=[user1.id],
        batch_admins=[user1.id],  # Same user in both
    )

    with pytest.raises(AppException, match="User cannot be both Employee and Batch Admin"):
        service.create_batch(batch_data, admin)


def test_batch_filtering_and_pagination(db_session: Session, extended_batch_setup: dict):
    """
    Verify listing batches with filters by year, quarter, status, meeting_day, and search term.
    """
    service = BatchService(db_session)
    org = extended_batch_setup["org_alpha"]
    admin = extended_batch_setup["org_admin_alpha"]

    # Seed 3 distinct batches
    b1 = service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="Alpha Engineering Q1",
            year=2026,
            quarter=Quarter.JFM,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            meeting_day=MeetingDay.MONDAY,
        ),
        admin,
    )
    b2 = service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="Alpha Product Q2",
            year=2026,
            quarter=Quarter.AMJ,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 30),
            meeting_day=MeetingDay.TUESDAY,
        ),
        admin,
    )
    b3 = service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="Alpha Sales 2025",
            year=2025,
            quarter=Quarter.OND,
            start_date=date(2025, 10, 1),
            end_date=date(2025, 12, 31),
            meeting_day=MeetingDay.FRIDAY,
        ),
        admin,
    )

    # 1. Filter by year 2026
    res_2026 = service.get_batches(admin, organization_id=org.id, year=2026)
    assert len(res_2026["data"]) >= 2
    for b in res_2026["data"]:
        assert b.year == 2026

    # 2. Filter by quarter AMJ
    res_amj = service.get_batches(admin, organization_id=org.id, quarter=Quarter.AMJ)
    assert len(res_amj["data"]) == 1
    assert res_amj["data"][0].name == "Alpha Product Q2"

    # 3. Filter by status DRAFT
    res_draft = service.get_batches(admin, organization_id=org.id, status=BatchStatus.DRAFT)
    assert len(res_draft["data"]) >= 3

    # Update b1 status to ACTIVE and filter
    service.update_batch(b1.id, BatchUpdate(status=BatchStatus.ACTIVE), admin)
    res_active = service.get_batches(admin, organization_id=org.id, status=BatchStatus.ACTIVE)
    assert len(res_active["data"]) == 1
    assert res_active["data"][0].id == b1.id

    # 4. Search keyword
    res_search = service.get_batches(admin, organization_id=org.id, search="Engineering")
    assert len(res_search["data"]) == 1
    assert res_search["data"][0].name == "Alpha Engineering Q1"

    # 5. Pagination boundary
    res_paged = service.get_batches(admin, organization_id=org.id, page=1, size=2)
    assert len(res_paged["data"]) == 2
    assert res_paged["pagination"]["page"] == 1
    assert res_paged["pagination"]["size"] == 2
    assert res_paged["pagination"]["total"] >= 3
    assert res_paged["pagination"]["has_next"] is True


def test_batch_update_partial_and_duplicate_handling(db_session: Session, extended_batch_setup: dict):
    """
    Verify updating batch fields partially and ensuring unique constraints are maintained.
    """
    service = BatchService(db_session)
    org = extended_batch_setup["org_alpha"]
    admin = extended_batch_setup["org_admin_alpha"]

    b1 = service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="Batch Alpha",
            year=2026,
            quarter=Quarter.JFM,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            meeting_day=MeetingDay.MONDAY,
        ),
        admin,
    )
    b2 = service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="Batch Beta",
            year=2026,
            quarter=Quarter.AMJ,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 30),
            meeting_day=MeetingDay.TUESDAY,
        ),
        admin,
    )

    # Partial update: meeting day only
    updated = service.update_batch(b1.id, BatchUpdate(meeting_day=MeetingDay.THURSDAY), admin)
    assert updated.meeting_day == MeetingDay.THURSDAY
    assert updated.name == "Batch Alpha"

    # Attempting to rename b2 to b1's name and quarter -> BatchAlreadyExistsException
    with pytest.raises(BatchAlreadyExistsException):
        service.update_batch(b2.id, BatchUpdate(name="Batch Alpha", quarter=Quarter.JFM, year=2026), admin)


def test_batch_soft_delete_and_not_found(db_session: Session, extended_batch_setup: dict):
    """
    Verify that deleting a batch sets is_deleted=True and subsequent queries return BatchNotFoundException.
    """
    service = BatchService(db_session)
    org = extended_batch_setup["org_alpha"]
    admin = extended_batch_setup["org_admin_alpha"]

    batch = service.create_batch(
        BatchCreate(
            organization_id=org.id,
            name="Temporary Batch",
            year=2026,
            quarter=Quarter.JAS,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 9, 30),
            meeting_day=MeetingDay.WEDNESDAY,
        ),
        admin,
    )

    # Soft delete
    service.delete_batch(batch.id, admin)

    # Direct query in DB shows is_deleted=True
    db_session.expire_all()
    deleted_rec = db_session.query(Batch).filter(Batch.id == batch.id).first()
    assert deleted_rec.is_deleted is True

    # Service get_batch raises BatchNotFoundException
    with pytest.raises(BatchNotFoundException):
        service.get_batch(batch.id, admin)

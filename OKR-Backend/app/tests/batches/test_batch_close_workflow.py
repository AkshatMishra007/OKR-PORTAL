"""
Comprehensive test suite for Batch Close & Read-Only Workflow.
"""

from datetime import date, datetime, UTC
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.common.exceptions import AppException, ForbiddenException

from app.batches.models import Batch, BatchMember, BatchStatus, MeetingDay, Quarter
from app.batches.schemas import BatchCreate, BatchUpdate
from app.batches.service import BatchService
from app.fogs_hurdles.schemas import FogsHurdleCreate, FogsHurdleUpdate
from app.fogs_hurdles.service import FogsHurdleService
from app.my_okr.models import OKR
from app.my_okr.schemas import OKRCreate, OKRUpdate
from app.my_okr.service import create_okr, delete_okr, update_okr, get_okrs
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.tracker_entries.schemas import TrackerEntryCreate
from app.tracker_entries.service import TrackerEntryService
from app.users.models import User
from app.weekly_update.schemas import WeeklyUpdateCreate
from app.weekly_update.service import WeeklyUpdateService


@pytest.fixture
def batch_close_data(db_session: Session):
    """
    Setup organization, open batch (AMJ 2026), second open batch (JAS 2026), roles, users, and memberships.
    """
    # 1. Organization
    org = Organization(name=f"Batch Close Test Org {uuid4().hex[:6]}", description="Close test org")
    db_session.add(org)
    db_session.commit()

    # 2. Roles
    org_admin_role = db_session.query(Role).filter(Role.name == "ORG_ADMIN").first()
    if not org_admin_role:
        org_admin_role = Role(name="ORG_ADMIN", description="Org Admin Role")
        db_session.add(org_admin_role)
        db_session.commit()

    emp_role = db_session.query(Role).filter(Role.name == "EMPLOYEE").first()
    if not emp_role:
        emp_role = Role(name="EMPLOYEE", description="Employee Role")
        db_session.add(emp_role)
        db_session.commit()

    # 3. Users
    admin_user = User(
        username=f"close_admin_{uuid4().hex[:6]}",
        email=f"close.admin.{uuid4().hex[:6]}@test.local",
        password_hash="testpasshash",
        first_name="Admin",
        last_name="CloseTest",
    )
    emp_user = User(
        username=f"close_emp_{uuid4().hex[:6]}",
        email=f"close.emp.{uuid4().hex[:6]}@test.local",
        password_hash="testpasshash",
        first_name="Employee",
        last_name="CloseTest",
    )
    db_session.add_all([admin_user, emp_user])
    db_session.commit()

    # 4. Organization Memberships
    admin_member = OrganizationMember(
        organization_id=org.id,
        user_id=admin_user.id,
        role_id=org_admin_role.id,
    )
    emp_member = OrganizationMember(
        organization_id=org.id,
        user_id=emp_user.id,
        role_id=emp_role.id,
    )
    db_session.add_all([admin_member, emp_member])
    db_session.commit()

    # 5. Open Batch 1 (AMJ 2026)
    batch_service = BatchService(db_session)
    amj_batch_data = BatchCreate(
        organization_id=org.id,
        name="AMJ 2026",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.MONDAY,
    )
    amj_batch = batch_service.create_batch(amj_batch_data, admin_user)
    amj_batch.status = BatchStatus.ACTIVE
    db_session.commit()

    # 6. Open Batch 2 (JAS 2026)
    jas_batch_data = BatchCreate(
        organization_id=org.id,
        name="JAS 2026",
        year=2026,
        quarter=Quarter.JAS,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 9, 30),
        meeting_day=MeetingDay.TUESDAY,
    )
    jas_batch = batch_service.create_batch(jas_batch_data, admin_user)
    jas_batch.status = BatchStatus.ACTIVE
    db_session.commit()

    # 7. Batch Memberships
    emp_batch_member = BatchMember(
        batch_id=amj_batch.id,
        user_id=emp_user.id,
        role_id=emp_role.id,
    )
    db_session.add(emp_batch_member)
    db_session.commit()

    return {
        "org": org,
        "amj_batch": amj_batch,
        "jas_batch": jas_batch,
        "admin_user": admin_user,
        "emp_user": emp_user,
        "admin_member": admin_member,
        "emp_member": emp_member,
        "batch_service": batch_service,
    }


def test_open_batch_editable_and_accepts_records(db_session: Session, batch_close_data: dict):
    """
    Verify open batch (AMJ 2026) can receive new OKRs, weekly updates, tracker entries, and can be edited.
    """
    d = batch_close_data
    amj_batch = d["amj_batch"]
    emp_user = d["emp_user"]
    emp_member = d["emp_member"]

    # Create OKR under open batch
    okr_data = OKRCreate(
        batch_id=amj_batch.id,
        assigned_to=emp_member.id,
        objective="Open Batch Objective",
        target="80%",
        key_results="Key Result 1",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    okr = create_okr(db_session, okr_data, emp_user, emp_member)
    assert okr.id is not None
    assert okr.batch_id == amj_batch.id

    # Add Weekly Update under open batch
    wu_service = WeeklyUpdateService(db_session)
    wu = wu_service.create_weekly_update(
        okr.id,
        WeeklyUpdateCreate(week_number=1, progress=50, remarks="Progressing"),
        emp_user,
    )
    assert wu.id is not None

    # Add Tracker Entry under open batch
    tr_service = TrackerEntryService(db_session)
    tr = tr_service.create_tracker_entry(
        okr.id,
        TrackerEntryCreate(week_start=date(2026, 4, 6), opportunities_received=10, opportunities_completed=5),
        emp_user,
    )
    assert tr.id is not None

    # Update OKR under open batch
    updated_okr = update_okr(db_session, okr.id, OKRUpdate(target="90%"), emp_user)
    assert updated_okr.target == "90%"


def test_close_batch_workflow(db_session: Session, batch_close_data: dict):
    """
    Verify authorized user can close an open batch, updating status to CLOSED and storing closed_at and closed_by.
    """
    d = batch_close_data
    amj_batch = d["amj_batch"]
    admin_user = d["admin_user"]
    batch_service = d["batch_service"]

    # Close AMJ 2026 batch
    res = batch_service.close_batch(amj_batch.id, admin_user)
    assert "data" in res
    closed_data = res["data"]
    assert closed_data["status"] == BatchStatus.CLOSED
    assert closed_data["closed_by"] == admin_user.id
    assert closed_data["closed_at"] is not None

    # Refresh DB session & verify persisted closed state
    db_session.expire_all()
    reloaded_batch = db_session.query(Batch).filter(Batch.id == amj_batch.id).first()
    assert reloaded_batch.status == BatchStatus.CLOSED
    assert reloaded_batch.closed_by == admin_user.id


def test_closed_batch_rejects_okr_mutations(db_session: Session, batch_close_data: dict):
    """
    Verify that once AMJ 2026 is closed:
    - Creating an OKR is rejected.
    - Updating an existing OKR is rejected.
    - Deleting an existing OKR is rejected.
    """
    d = batch_close_data
    amj_batch = d["amj_batch"]
    emp_user = d["emp_user"]
    emp_member = d["emp_member"]
    batch_service = d["batch_service"]

    # 1. Create OKR before closing
    okr_data = OKRCreate(
        batch_id=amj_batch.id,
        assigned_to=emp_member.id,
        objective="Pre-Close Objective",
        target="80%",
        key_results="Pre-Close KR",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    okr = create_okr(db_session, okr_data, emp_user, emp_member)

    # 2. Close Batch
    batch_service.close_batch(amj_batch.id, d["admin_user"])

    # 3. Try to Create OKR under closed batch -> Should be rejected
    new_okr_data = OKRCreate(
        batch_id=amj_batch.id,
        assigned_to=emp_member.id,
        objective="Post-Close Objective",
        target="100%",
        key_results="Post-Close KR",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    # 3. Try to Create OKR under closed batch -> Should be rejected
    new_okr_data = OKRCreate(
        batch_id=amj_batch.id,
        assigned_to=emp_member.id,
        objective="Post-Close Objective",
        target="100%",
        key_results="Post-Close KR",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    with pytest.raises((HTTPException, ForbiddenException)) as exc_info:
        create_okr(db_session, new_okr_data, emp_user, emp_member)
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg

    # 4. Try to Update existing OKR -> Should be rejected
    with pytest.raises((HTTPException, ForbiddenException)) as exc_info:
        update_okr(db_session, okr.id, OKRUpdate(target="100%"), emp_user)
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg

    # 5. Try to Delete existing OKR -> Should be rejected
    with pytest.raises((HTTPException, ForbiddenException)) as exc_info:
        delete_okr(db_session, okr.id, emp_user)
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg


def test_closed_batch_rejects_subresource_mutations(db_session: Session, batch_close_data: dict):
    """
    Verify creating weekly updates, tracker entries, and fogs/hurdles under a closed batch is rejected.
    """
    d = batch_close_data
    amj_batch = d["amj_batch"]
    emp_user = d["emp_user"]
    emp_member = d["emp_member"]
    batch_service = d["batch_service"]

    # Create OKR
    okr_data = OKRCreate(
        batch_id=amj_batch.id,
        assigned_to=emp_member.id,
        objective="Subresource Test Objective",
        target="80%",
        key_results="KR",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    okr = create_okr(db_session, okr_data, emp_user, emp_member)

    # Close Batch
    batch_service.close_batch(amj_batch.id, d["admin_user"])

    # Weekly Update Creation -> Rejected
    wu_service = WeeklyUpdateService(db_session)
    with pytest.raises((HTTPException, ForbiddenException)) as exc_info:
        wu_service.create_weekly_update(
            okr.id,
            WeeklyUpdateCreate(week_number=1, progress=60, remarks="Weekly update on closed batch"),
            emp_user,
        )
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg

    # Tracker Entry Creation -> Rejected
    tr_service = TrackerEntryService(db_service=db_session) if hasattr(TrackerEntryService, "db_service") else TrackerEntryService(db_session)
    with pytest.raises((HTTPException, ForbiddenException)) as exc_info:
        tr_service.create_tracker_entry(
            okr.id,
            TrackerEntryCreate(week_start=date(2026, 4, 13), opportunities_received=20, opportunities_completed=10),
            emp_user,
        )
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg

    # Fogs & Hurdles Creation -> Rejected
    fh_service = FogsHurdleService(db_session)
    with pytest.raises((HTTPException, ForbiddenException)) as exc_info:
        fh_service.create_fogs_hurdle(
            okr.id,
            FogsHurdleCreate(fogs_hurdles="Blocker", action_points="Action"),
            emp_user,
        )
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg


def test_closed_batch_data_remains_viewable_and_other_batch_editable(db_session: Session, batch_close_data: dict):
    """
    Verify:
    1. Closed batch data (OKRs) remains viewable.
    2. Another open batch (JAS 2026) remains fully editable and accepts new OKRs.
    """
    d = batch_close_data
    amj_batch = d["amj_batch"]
    jas_batch = d["jas_batch"]
    emp_user = d["emp_user"]
    emp_member = d["emp_member"]
    batch_service = d["batch_service"]

    # 1. Create OKR under AMJ 2026
    okr_data = OKRCreate(
        batch_id=amj_batch.id,
        assigned_to=emp_member.id,
        objective="AMJ Historical Objective",
        target="100%",
        key_results="Historical KR",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    amj_okr = create_okr(db_session, okr_data, emp_user, emp_member)

    # 2. Close AMJ 2026
    batch_service.close_batch(amj_batch.id, d["admin_user"])

    # 3. View OKRs for AMJ 2026 -> Success (Historical data viewable)
    list_res = get_okrs(db_session, current_user=emp_user, current_membership=emp_member, batch_id=amj_batch.id)
    assert len(list_res["data"]) >= 1
    objectives = [o.objective for o in list_res["data"]]
    assert "AMJ Historical Objective" in objectives

    # 4. Create OKR under open JAS 2026 batch -> Success (Other open batch remains editable)
    jas_okr_data = OKRCreate(
        batch_id=jas_batch.id,
        assigned_to=emp_member.id,
        objective="JAS Active Objective",
        target="100%",
        key_results="JAS Active KR",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    jas_okr = create_okr(db_session, jas_okr_data, emp_user, emp_member)
    assert jas_okr.id is not None
    assert jas_okr.batch_id == jas_batch.id


def test_closed_batch_rejects_fogs_hurdles_update_and_delete(db_session: Session, batch_close_data: dict):
    """
    Verify updating and deleting existing FOGS & Hurdles under a closed batch is rejected with 400 Bad Request.
    """
    d = batch_close_data
    amj_batch = d["amj_batch"]
    emp_user = d["emp_user"]
    emp_member = d["emp_member"]
    batch_service = d["batch_service"]

    # 1. Create OKR before closing
    okr_data = OKRCreate(
        batch_id=amj_batch.id,
        assigned_to=emp_member.id,
        objective="Hurdle Immutability Objective",
        target="80%",
        key_results="KR",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    okr = create_okr(db_session, okr_data, emp_user, emp_member)

    # 2. Create FOGS & Hurdle before closing
    fh_service = FogsHurdleService(db_session)
    hurdle = fh_service.create_fogs_hurdle(
        okr.id,
        FogsHurdleCreate(fogs_hurdles="Pre-close blocker", action_points="Pre-close action"),
        emp_user,
    )
    assert hurdle.id is not None

    # 3. Close Batch
    batch_service.close_batch(amj_batch.id, d["admin_user"])

    # 4. Try updating hurdle -> Rejected
    with pytest.raises((HTTPException, ForbiddenException, AppException)) as exc_info:
        fh_service.update_fogs_hurdle(
            hurdle.id,
            FogsHurdleUpdate(fogs_hurdles="Attempted post-close update"),
            emp_user,
        )
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg or "closed and read-only" in err_msg

    # 5. Try deleting hurdle -> Rejected
    with pytest.raises((HTTPException, ForbiddenException, AppException)) as exc_info:
        fh_service.delete_fogs_hurdle(hurdle.id, emp_user)
    err_msg = getattr(exc_info.value, "detail", getattr(exc_info.value, "message", str(exc_info.value)))
    assert "AMJ 2026 batch is closed and read-only" in err_msg or "closed and read-only" in err_msg


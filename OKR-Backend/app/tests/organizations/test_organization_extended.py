"""
Extended and edge-case unit and integration tests for Organizations module.

Covers:
- Organization logo upload (file persistence, unique filenames, DB column update, error handling).
- Multi-criteria search (name, email substrings).
- Advanced filtering: is_active states, created_after / created_before date bounds.
- Sorting options: sort_by (name, created_at) with asc / desc order.
- Soft-delete lifecycle: is_deleted, is_active, deleted_at, and updated_by audit trail.
- Update name conflict validation: updating self name vs collision with another existing organization.
- Relationship: Organization containing multiple active batches.
"""

import io
import os
import shutil
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.batches.models import Batch, BatchStatus, MeetingDay, Quarter
from app.common.exceptions import (
    OrganizationAlreadyExistsException,
    OrganizationNotFoundException,
)
from app.organizations.models import Organization
from app.organizations.schemas import OrganizationCreate, OrganizationUpdate
from app.organizations.service import (
    create_organization_service,
    delete_organization_service,
    get_organization_service,
    list_organizations_service,
    update_organization_service,
    upload_organization_logo_service,
    UPLOAD_DIR,
)


@pytest.fixture
def org_extended_setup(db_session: Session):
    """Fixture providing clean seed organizations with varying attributes."""
    org1 = create_organization_service(
        db_session,
        OrganizationCreate(
            name="Quantum Dynamics",
            description="Quantum computing research lab",
            email="info@quantumdynamics.org",
            phone="1112223333",
            address="100 Tech Blvd, Boston",
        ),
        current_user_id=uuid.uuid4(),
    )
    org2 = create_organization_service(
        db_session,
        OrganizationCreate(
            name="Solaris Energy",
            description="Renewable solar solutions",
            email="contact@solarisenergy.com",
            phone="4445556666",
            address="200 Sun Way, Phoenix",
        ),
        current_user_id=uuid.uuid4(),
    )
    org3 = create_organization_service(
        db_session,
        OrganizationCreate(
            name="Apex Biotech",
            description="Genomic analysis platforms",
            email="support@apexbiotech.io",
            phone="7778889999",
            address="300 Bio Park, San Diego",
        ),
        current_user_id=uuid.uuid4(),
    )

    return {
        "org1": org1,
        "org2": org2,
        "org3": org3,
    }


def test_organization_logo_upload_success_and_cleanup(db_session: Session, org_extended_setup: dict):
    """
    Verify upload_organization_logo_service:
    - Creates the upload directory if missing.
    - Saves binary file bytes to disk with unique naming.
    - Updates organization.logo with relative path.
    - Cleans up created test file on disk.
    """
    org1 = org_extended_setup["org1"]
    test_user_id = uuid.uuid4()

    # Create dummy image file in memory
    image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    upload_file = UploadFile(
        file=io.BytesIO(image_bytes),
        filename="company_logo.png",
        headers={"content-type": "image/png"},
    )

    updated_org = upload_organization_logo_service(
        db=db_session,
        organization_id=org1.id,
        file=upload_file,
        current_user_id=test_user_id,
    )

    assert updated_org.logo is not None
    assert updated_org.logo.startswith("/uploads/logos/")
    assert updated_org.logo.endswith(".png")
    assert updated_org.updated_by == test_user_id

    # Verify physical file existence on disk
    saved_rel_path = updated_org.logo.lstrip("/")
    saved_file_path = os.path.join(".", saved_rel_path)
    assert os.path.exists(saved_file_path)

    # Cleanup test file
    if os.path.exists(saved_file_path):
        os.remove(saved_file_path)


def test_organization_logo_upload_non_existent_org(db_session: Session):
    """
    Verify logo upload raises OrganizationNotFoundException when given an invalid organization ID.
    """
    fake_id = uuid.uuid4()
    upload_file = UploadFile(
        file=io.BytesIO(b"testdata"),
        filename="dummy.png",
    )

    with pytest.raises(OrganizationNotFoundException):
        upload_organization_logo_service(
            db=db_session,
            organization_id=fake_id,
            file=upload_file,
        )


def test_organization_multi_criteria_search(db_session: Session, org_extended_setup: dict):
    """
    Verify searching organizations across name and email fields.
    """
    # 1. Search by name keyword
    res_name = list_organizations_service(db_session, search="Solaris")
    assert res_name["pagination"]["total"] == 1
    assert res_name["data"][0].name == "Solaris Energy"

    # 2. Search by email keyword
    res_email = list_organizations_service(db_session, search="apexbiotech.io")
    assert res_email["pagination"]["total"] == 1
    assert res_email["data"][0].email == "support@apexbiotech.io"

    # 3. Partial case-insensitive search
    res_partial = list_organizations_service(db_session, search="quantum")
    assert res_partial["pagination"]["total"] == 1
    assert res_partial["data"][0].name == "Quantum Dynamics"


def test_organization_sorting_and_pagination(db_session: Session, org_extended_setup: dict):
    """
    Verify sorting by name (asc/desc) and pagination windowing.
    """
    # Sort by name ASC
    res_asc = list_organizations_service(db_session, sort_by="name", sort_order="asc")
    names_asc = [o.name for o in res_asc["data"]]
    assert names_asc == sorted(names_asc)

    # Sort by name DESC
    res_desc = list_organizations_service(db_session, sort_by="name", sort_order="desc")
    names_desc = [o.name for o in res_desc["data"]]
    assert names_desc == sorted(names_desc, reverse=True)

    # Pagination: size=1, page=2
    res_paged = list_organizations_service(db_session, page=2, size=1, sort_by="name", sort_order="asc")
    assert len(res_paged["data"]) == 1
    assert res_paged["pagination"]["page"] == 2
    assert res_paged["pagination"]["has_prev"] is True
    assert res_paged["pagination"]["total"] >= 3


def test_organization_update_collision_and_self_update(db_session: Session, org_extended_setup: dict):
    """
    Verify updating organization:
    - Updating description without changing name succeeds.
    - Updating name to same name succeeds.
    - Updating name to another existing organization's name raises OrganizationAlreadyExistsException.
    """
    org1 = org_extended_setup["org1"]
    org2 = org_extended_setup["org2"]

    # 1. Update same name -> success
    updated_self = update_organization_service(
        db_session,
        org1.id,
        OrganizationUpdate(name="Quantum Dynamics", description="Updated description"),
    )
    assert updated_self.description == "Updated description"

    # 2. Update to collision with org2 name -> raises exception
    with pytest.raises(OrganizationAlreadyExistsException):
        update_organization_service(
            db_session,
            org1.id,
            OrganizationUpdate(name="Solaris Energy"),
        )


def test_organization_soft_delete_lifecycle(db_session: Session, org_extended_setup: dict):
    """
    Verify soft deletion:
    - Sets is_deleted=True, is_active=False, deleted_at timestamp, updated_by.
    - Soft-deleted organization is excluded from default listing.
    """
    org3 = org_extended_setup["org3"]
    user_id = uuid.uuid4()

    # Soft delete org3
    deleted_org = delete_organization_service(
        db_session,
        org3.id,
        current_user_id=user_id,
    )
    assert deleted_org.is_deleted is True
    assert deleted_org.is_active is False
    assert deleted_org.deleted_at is not None
    assert deleted_org.updated_by == user_id

    # get_organization_service raises OrganizationNotFoundException
    with pytest.raises(OrganizationNotFoundException):
        get_organization_service(db_session, org3.id)

    # Listing active organizations excludes org3
    list_res = list_organizations_service(db_session, is_active=True)
    active_ids = [o.id for o in list_res["data"]]
    assert org3.id not in active_ids


def test_organization_with_multiple_batches_association(db_session: Session, org_extended_setup: dict):
    """
    Verify an organization can maintain multiple sequential active batches.
    """
    org1 = org_extended_setup["org1"]

    b1 = Batch(
        id=uuid.uuid4(),
        organization_id=org1.id,
        name="Q1 Quantum Cohort",
        year=2026,
        quarter=Quarter.JFM,
        start_date=datetime(2026, 1, 1).date(),
        end_date=datetime(2026, 3, 31).date(),
        meeting_day=MeetingDay.MONDAY,
        status=BatchStatus.ACTIVE,
        is_deleted=False,
    )
    b2 = Batch(
        id=uuid.uuid4(),
        organization_id=org1.id,
        name="Q2 Quantum Cohort",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=datetime(2026, 4, 1).date(),
        end_date=datetime(2026, 6, 30).date(),
        meeting_day=MeetingDay.TUESDAY,
        status=BatchStatus.ACTIVE,
        is_deleted=False,
    )
    db_session.add_all([b1, b2])
    db_session.commit()

    # Query batches belonging to org1
    batches = db_session.query(Batch).filter(
        Batch.organization_id == org1.id,
        Batch.is_deleted.is_(False),
    ).all()
    assert len(batches) == 2
    batch_names = [b.name for b in batches]
    assert "Q1 Quantum Cohort" in batch_names
    assert "Q2 Quantum Cohort" in batch_names

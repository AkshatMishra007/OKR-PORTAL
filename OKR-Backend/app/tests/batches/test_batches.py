import uuid
import pytest
from datetime import date
from fastapi import status
from app.batches.models import Batch, Quarter, MeetingDay
from app.organizations.models import Organization
from app.batches.schemas import BatchCreate, BatchUpdate
from app.batches.service import BatchService
from app.common.exceptions import (
    BatchAlreadyExistsException,
    BatchNotFoundException,
    OrganizationNotFoundException,
)


@pytest.fixture
def sample_org(db_session):
    org = Organization(
        name="Batches Org",
        is_active=True,
        is_deleted=False,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


def test_batch_service_and_repository(db_session, sample_org, test_user):
    service = BatchService(db_session)

    # Create Batch
    create_data = BatchCreate(
        organization_id=sample_org.id,
        name="Q1 Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )

    batch = service.create_batch(create_data, test_user)
    assert batch.id is not None
    assert batch.name == "Q1 Batch"

    # Duplicate creation exception
    with pytest.raises(BatchAlreadyExistsException):
        service.create_batch(create_data, test_user)

    # Get Batch by ID
    fetched = service.get_batch(batch.id, test_user)
    assert fetched["data"]["id"] == batch.id


    # Get Batches List & Search
    res = service.get_batches(test_user, organization_id=sample_org.id, search="2026")
    assert res["pagination"]["total"] == 1
    assert len(res["data"]) == 1

    # Update Batch
    update_data = BatchUpdate(name="Q1 Updated Batch")
    updated = service.update_batch(batch.id, update_data, test_user)
    assert updated.name == "Q1 Updated Batch"

    # Duplicate update exception
    b2_data = BatchCreate(
        organization_id=sample_org.id,
        name="Q2 Batch",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.MONDAY,
    )
    b2 = service.create_batch(b2_data, test_user)
    with pytest.raises(BatchAlreadyExistsException):
        service.update_batch(b2.id, BatchUpdate(name="Q1 Updated Batch", quarter=Quarter.JFM), test_user)

    # Delete Batch
    service.delete_batch(batch.id, test_user)

    # Get Deleted Batch raises NotFound
    with pytest.raises(BatchNotFoundException):
        service.get_batch(batch.id, test_user)


def test_batch_service_exceptions(db_session, test_user):
    service = BatchService(db_session)
    invalid_id = uuid.uuid4()

    create_data = BatchCreate(
        organization_id=invalid_id,
        name="Invalid Org Batch",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
    )
    with pytest.raises(OrganizationNotFoundException):
        service.create_batch(create_data, test_user)

    with pytest.raises(BatchNotFoundException):
        service.get_batch(invalid_id, test_user)

    with pytest.raises(BatchNotFoundException):
        service.update_batch(invalid_id, BatchUpdate(name="Test"), test_user)

    with pytest.raises(BatchNotFoundException):
        service.delete_batch(invalid_id, test_user)


def test_batch_router(client, sample_org, auth_headers):
    # POST /batches/
    res = client.post(
        "/batches/",
        json={
            "organization_id": str(sample_org.id),
            "name": "Router Batch",
            "year": 2026,
            "quarter": "JFM",
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "meeting_day": "MONDAY",
        },
        headers=auth_headers,
    )
    assert res.status_code == status.HTTP_201_CREATED
    batch_id = res.json()["id"]

    # GET /batches/
    res = client.get(f"/batches/?organization_id={sample_org.id}", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK

    # GET /batches/{batch_id}
    res = client.get(f"/batches/{batch_id}", headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK

    # PUT /batches/{batch_id}
    res = client.put(
        f"/batches/{batch_id}",
        json={"name": "Updated Router Batch"},
        headers=auth_headers,
    )
    assert res.status_code == status.HTTP_200_OK

    # DELETE /batches/{batch_id}
    res = client.delete(f"/batches/{batch_id}", headers=auth_headers)
    assert res.status_code == status.HTTP_204_NO_CONTENT


from datetime import datetime, timezone
import uuid
from unittest.mock import MagicMock, patch

from app.organization_members.models import OrganizationMember
from app.common.exceptions import OrganizationMemberNotFoundException


# ==========================================================
# POST /organization-members
# ==========================================================


@patch("app.organization_members.router.create_member_service")
def test_tc_01_create_member_success(mock_service, client):
    """
    Verify member creation endpoint.
    """

    now = datetime.now(timezone.utc)
    member_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()

    service_response = OrganizationMember(
        id=member_id,
        organization_id=organization_id,
        user_id=user_id,
        role_id=role_id,
        joined_at=now,
        is_active=True,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )

    mock_service.return_value = service_response

    payload = {
        "organization_id": str(organization_id),
        "user_id": str(user_id),
        "role_id": str(role_id),
    }

    response = client.post(
        "/organization-members",
        json=payload,
    )

    assert response.status_code == 201
    assert response.json()["organization_id"] == str(organization_id)


def test_tc_02_create_member_invalid_payload(client):
    """
    Verify validation error.
    """

    response = client.post(
        "/organization-members",
        json={},
    )

    assert response.status_code == 422


# ==========================================================
# GET /organization-members/{id}
# ==========================================================


@patch("app.organization_members.router.get_member_service")
def test_tc_03_get_member_success(mock_service, client):
    """
    Verify fetching a member.
    """

    now = datetime.now(timezone.utc)
    member_id = uuid.uuid4()

    member = OrganizationMember(
        id=member_id,
        organization_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_id=uuid.uuid4(),
        joined_at=now,
        is_active=True,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )

    mock_service.return_value = member

    response = client.get(
        f"/organization-members/{member_id}"
    )

    assert response.status_code == 200


@patch("app.organization_members.router.get_member_service")
def test_tc_04_get_member_not_found(mock_service, client):
    """
    Verify not found response.
    """

    mock_service.side_effect = OrganizationMemberNotFoundException("Organization member not found.")

    response = client.get(
        f"/organization-members/{uuid.uuid4()}"
    )

    assert response.status_code == 404


# ==========================================================
# GET /organization-members
# ==========================================================


@patch("app.organization_members.router.list_members_service")
def test_tc_05_list_members_success(mock_service, client):
    """
    Verify list endpoint.
    """

    service_response = {
        "data": [],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 0,
        },
    }

    mock_service.return_value = service_response

    response = client.get(
        "/organization-members"
    )

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] == 0


# ==========================================================
# PUT /organization-members/{id}
# ==========================================================


@patch("app.organization_members.router.update_member_service")
def test_tc_06_update_member_success(mock_service, client):
    """
    Verify update endpoint.
    """

    now = datetime.now(timezone.utc)
    member_id = str(uuid.uuid4())
    role_id = str(uuid.uuid4())

    updated = OrganizationMember(
        id=uuid.UUID(member_id),
        organization_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_id=uuid.UUID(role_id),
        joined_at=now,
        is_active=True,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )

    mock_service.return_value = updated

    response = client.put(
        f"/organization-members/{member_id}",
        json={
            "role_id": role_id
        },
    )

    assert response.status_code == 200


def test_tc_07_update_invalid_payload(client):
    """
    Verify validation error.
    """

    response = client.put(
        f"/organization-members/{uuid.uuid4()}",
        json={
            "role_id": "invalid-uuid"
        },
    )

    assert response.status_code == 422


# ==========================================================
# DELETE /organization-members/{id}
# ==========================================================


@patch("app.organization_members.router.delete_member_service")
def test_tc_08_delete_member_success(mock_delete_service, client):
    """
    Verify delete endpoint.
    """

    now = datetime.now(timezone.utc)
    member_id = str(uuid.uuid4())

    deleted = OrganizationMember(
        id=uuid.UUID(member_id),
        organization_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_id=uuid.uuid4(),
        joined_at=now,
        is_active=False,
        is_deleted=True,
        created_at=now,
        updated_at=now,
    )

    mock_delete_service.return_value = deleted

    response = client.delete(
        f"/organization-members/{member_id}"
    )

    mock_delete_service.assert_called_once()

    assert response.status_code == 200


@patch("app.organization_members.router.delete_member_service")
def test_tc_09_delete_member_not_found(mock_service, client):
    """
    Verify delete missing member.
    """

    mock_service.side_effect = OrganizationMemberNotFoundException(
        "Organization member not found"
    )

    response = client.delete(
        f"/organization-members/{uuid.uuid4()}"
    )

    assert response.status_code == 404


# ==========================================================
# Filtering & Pagination Query Parameters
# ==========================================================


@patch("app.organization_members.router.list_members_service")
def test_tc_10_list_members_filters(mock_service, client):
    """
    Verify list endpoint with filters.
    """

    organization_id = str(uuid.uuid4())

    mock_service.return_value = {
        "data": [],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 0,
        },
    }

    response = client.get(
        f"/organization-members?organization_id={organization_id}"
    )

    assert response.status_code == 200


def test_tc_11_invalid_page(client):
    """
    Query parameter validation.
    """

    response = client.get(
        "/organization-members?page=0"
    )

    assert response.status_code == 422


def test_tc_12_invalid_size(client):
    """
    Query parameter validation.
    """

    response = client.get(
        "/organization-members?size=0"
    )

    assert response.status_code == 422
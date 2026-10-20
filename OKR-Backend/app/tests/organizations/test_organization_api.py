import uuid
import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.main import app
from app.users.models import User

from app.core.database import get_db

client = TestClient(app)


def override_get_db(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


@pytest.fixture(autouse=True)
def mock_auth(db_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db(db_session)
    from app.organizations.models import Organization
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    ssdn_org = Organization(name="SSDN Organization")
    db_session.add(ssdn_org)
    db_session.commit()
    db_session.refresh(ssdn_org)

    super_admin_role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(super_admin_role)
    db_session.commit()
    db_session.refresh(super_admin_role)

    mock_user = User(
        id=uuid.uuid4(),
        username="superadmin",
        email="superadmin@ssdn.com",
        password_hash="hashedpass",
        first_name="Super",
        last_name="Admin",
        is_deleted=False,
    )
    db_session.add(mock_user)
    db_session.commit()
    db_session.refresh(mock_user)

    member = OrganizationMember(
        organization_id=ssdn_org.id,
        user_id=mock_user.id,
        role_id=super_admin_role.id,
    )
    db_session.add(member)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()


def test_create_organization():

    response = client.post(
        "/api/organizations/",
        json={
            "name": "SSDN Technologies",
            "description": "OKR Platform",
            "email": "contact@ssdn.com",
            "phone": "9999999999",
            "address": "India",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["phone"] == "9999999999"
    assert data["email"] == "contact@ssdn.com"


def test_create_duplicate_organization():

    client.post(
        "/api/organizations/",
        json={
            "name": "Duplicate Org",
        },
    )

    response = client.post(
        "/api/organizations/",
        json={
            "name": "Duplicate Org",
        },
    )

    assert response.status_code == 400


def test_get_organization():

    create = client.post(
        "/api/organizations/",
        json={
            "name": "Get Org",
        },
    )

    organization_id = create.json()["id"]

    response = client.get(
        f"/api/organizations/{organization_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == organization_id


def test_list_organizations():

    client.post(
        "/api/organizations/",
        json={
            "name": "List Test Org",
            "email": "list@test.com",
            "phone": "8888888888",
            "address": "123 Street",
        },
    )

    response = client.get(
        "/api/organizations/"
    )

    assert response.status_code == 200

    data = response.json()

    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) > 0
    # Verify fields like phone, email, address are returned in list items
    first_item = data["data"][0]
    assert "phone" in first_item
    assert "email" in first_item
    assert "address" in first_item
    assert "is_active" in first_item


def test_update_organization():

    create = client.post(
        "/api/organizations/",
        json={
            "name": "Old Name",
        },
    )

    organization_id = create.json()["id"]

    response = client.put(
        f"/api/organizations/{organization_id}",
        json={
            "name": "New Name",
            "description": "Updated",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Name"


def test_delete_organization():

    create = client.post(
        "/api/organizations/",
        json={
            "name": "Delete Org",
        },
    )

    organization_id = create.json()["id"]

    response = client.delete(
        f"/api/organizations/{organization_id}"
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


def test_list_organizations_with_search():

    client.post(
        "/api/organizations/",
        json={
            "name": "Searchable Org",
        },
    )

    response = client.get(
        "/api/organizations/?search=Searchable"
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["pagination"]["total"] >= 1


def test_upload_organization_logo_api():
    create = client.post(
        "/api/organizations/",
        json={
            "name": "Logo Test Org",
        },
    )
    assert create.status_code == 201
    org_id = create.json()["id"]

    file_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("test_logo.png", file_content, "image/png")}

    response = client.post(
        f"/api/organizations/{org_id}/logo",
        files=files,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["logo"] is not None
    assert data["logo"].startswith("/uploads/logos/")
    assert data["logo"].endswith(".png")


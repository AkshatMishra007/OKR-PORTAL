import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User

client = TestClient(app)


def override_get_db(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass

    return _override


from app.auth.dependencies import get_current_user
from app.tests.conftest import override_get_current_user


@pytest.fixture(autouse=True)
def setup_db_override(db_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def sample_org(db_session):
    org = Organization(
        id=uuid.uuid4(),
        name="Test Org",
        is_deleted=False,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def sample_user(db_session):
    user = User(
        id=uuid.uuid4(),
        username=f"user_{uuid.uuid4().hex[:6]}",
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashed",
        first_name="Test",
        is_deleted=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def generic_role(db_session):
    role = Role(
        id=uuid.uuid4(),
        name="Member",
        description="Generic member role",
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


# ==========================================================
# Creation Tests
# ==========================================================

def test_create_member_generic_role(sample_org, sample_user, generic_role):
    response = client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": str(sample_user.id),
            "role_id": str(generic_role.id),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["role_id"] == str(generic_role.id)
    assert data["batch_id"] is None
    assert data["role"]["name"] == "Member"


def test_create_duplicate_member_fails(sample_org, sample_user, generic_role):
    client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": str(sample_user.id),
            "role_id": str(generic_role.id),
        },
    )

    response = client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": str(sample_user.id),
            "role_id": str(generic_role.id),
        },
    )

    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()



def test_create_member_invalid_organization_returns_404(sample_user, generic_role):
    invalid_org_id = str(uuid.uuid4())
    response = client.post(
        "/api/organization-members",
        json={
            "organization_id": invalid_org_id,
            "user_id": str(sample_user.id),
            "role_id": str(generic_role.id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found"


def test_create_member_invalid_user_returns_404(sample_org, generic_role):
    invalid_user_id = str(uuid.uuid4())
    response = client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": invalid_user_id,
            "role_id": str(generic_role.id),
        },
    )

    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_create_member_invalid_role_id_returns_404(sample_org, sample_user):
    invalid_role_id = str(uuid.uuid4())
    response = client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": str(sample_user.id),
            "role_id": invalid_role_id,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found"


# ==========================================================
# Delete & Query Tests
# ==========================================================

def test_soft_delete_member_success(sample_org, sample_user, generic_role):
    create = client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": str(sample_user.id),
            "role_id": str(generic_role.id),
        },
    )
    member_id = create.json()["id"]

    delete_resp = client.delete(f"/api/organization-members/{member_id}")
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/api/organization-members/{member_id}")
    assert get_resp.status_code == 404


def test_list_members_with_role_filter(sample_org, sample_user, generic_role):
    client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": str(sample_user.id),
            "role_id": str(generic_role.id),
        },
    )

    response = client.get(f"/api/organization-members?role_id={generic_role.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["role_id"] == str(generic_role.id)


def test_list_members_pagination(sample_org, sample_user, generic_role):
    client.post(
        "/api/organization-members",
        json={
            "organization_id": str(sample_org.id),
            "user_id": str(sample_user.id),
            "role_id": str(generic_role.id),
        },
    )

    response = client.get("/api/organization-members?page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["size"] == 10
    assert data["pagination"]["total"] >= 1

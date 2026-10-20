from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.password import verify_password
from app.core.database import get_db
from app.main import app
from app.users.models import User


@pytest.fixture(autouse=True)
def client(db_session):
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db(db_session)
    mock_user = User(
        id=uuid4(),
        username="mockuser",
        email="mock@test.com",
        first_name="Mock",
        is_deleted=False,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with TestClient(app) as test_client:
        globals()["client"] = test_client
        yield test_client

    app.dependency_overrides.clear()


def override_get_db(db_session):

    def _override():
        try:
            yield db_session
        finally:
            pass

    return _override


@pytest.fixture
def test_org(db_session: Session):
    from app.organizations.models import Organization

    org = Organization(id=uuid4(), name="Test Router Org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_role(db_session: Session):
    from app.rbac.models import Role

    role = Role(id=uuid4(), name="Router Role")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


def create_payload(org_id=None, role_id=None):

    return {
        "username": "testuser",
        "email": "test@test.com",
        "password": "Password@123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "9999999999",
        "designation": "Developer",
        "description": "Testing user",
        "organization_id": str(org_id or uuid4()),
        "role_id": str(role_id or uuid4()),
    }


def test_create_user_success(db_session: Session, test_org, test_role):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    response = client.post(
        "/api/users/",
        json=create_payload(test_org.id, test_role.id),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "test@test.com"

    assert "password_hash" not in data


def test_password_is_hashed(db_session: Session, test_org, test_role):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    response = client.post(
        "/api/users/",
        json=create_payload(test_org.id, test_role.id),
    )

    assert response.status_code == 201

    user = db_session.query(User).filter(User.username == "testuser").first()

    assert user is not None

    assert user.password_hash != "Password@123"

    assert verify_password("Password@123", user.password_hash)


def test_create_user_invalid_organization(db_session: Session, test_role):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    payload = create_payload(uuid4(), test_role.id)

    response = client.post("/api/users/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found."


def test_create_user_invalid_role(db_session: Session, test_org):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    payload = create_payload(test_org.id, uuid4())

    response = client.post("/api/users/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found."


def test_duplicate_username(db_session: Session, test_org, test_role):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    payload1 = create_payload(test_org.id, test_role.id)

    client.post("/api/users/", json=payload1)

    payload2 = create_payload(test_org.id, test_role.id)

    payload2["email"] = "another@test.com"

    response = client.post("/api/users/", json=payload2)

    assert response.status_code == 400

    assert response.json()["detail"] == ("Username already exists.")


def test_duplicate_email(db_session: Session, test_org, test_role):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    payload1 = create_payload(test_org.id, test_role.id)

    client.post("/api/users/", json=payload1)

    payload2 = create_payload(test_org.id, test_role.id)

    payload2["username"] = "anotheruser"

    response = client.post("/api/users/", json=payload2)

    assert response.status_code == 400

    assert response.json()["detail"] == ("Email already exists.")


def test_create_user_invalid_email(test_org, test_role):

    response = client.post(
        "/api/users/",
        json={
            "username": "invalid",
            "email": "wrong-email",
            "password": "Password@123",
            "first_name": "Test",
            "organization_id": str(test_org.id),
            "role_id": str(test_role.id),
        },
    )

    assert response.status_code == 422


def test_create_user_without_first_name(test_org, test_role):

    response = client.post(
        "/api/users/",
        json={
            "username": "missingname",
            "email": "missing@test.com",
            "password": "Password@123",
            "organization_id": str(test_org.id),
            "role_id": str(test_role.id),
        },
    )

    assert response.status_code == 422


def test_create_user_optional_fields(db_session, test_org, test_role):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    response = client.post(
        "/api/users/",
        json={
            "username": "optional",
            "email": "optional@test.com",
            "password": "Password@123",
            "first_name": "Optional",
            "organization_id": str(test_org.id),
            "role_id": str(test_role.id),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "optional"

    assert data["last_name"] is None

    assert data["phone"] is None


def test_get_users_by_organization_api_endpoint(
    db_session: Session, test_org, test_role
):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    payload = create_payload(test_org.id, test_role.id)

    create_res = client.post("/api/users/", json=payload)
    assert create_res.status_code == 201

    response = client.get(f"/api/users/organization/{test_org.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert len(data["data"]) == 1

    assert data["data"][0]["username"] == "testuser"
    assert "role" not in data["data"][0]
    assert len(data["data"][0]["organization_memberships"]) == 1
    assert data["data"][0]["organization_memberships"][0]["organization_id"] == str(test_org.id)
    assert data["data"][0]["organization_memberships"][0]["role"]["id"] == str(test_role.id)
    assert data["data"][0]["organization_memberships"][0]["role"]["name"] == test_role.name



def test_get_current_user_success(db_session: Session):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    user = User(
        username="john",
        email="john@test.com",
        password_hash="hashed",
        first_name="John",
        last_name="Doe",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/users/me")

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "john"

    assert data["email"] == "john@test.com"

    app.dependency_overrides.clear()


def test_get_current_user_without_token():

    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/api/users/me")

    assert response.status_code == 401


def test_get_user_by_id(db_session: Session):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    user = User(
        username="getuser",
        email="get@test.com",
        password_hash="hash",
        first_name="Get",
    )

    db_session.add(user)

    db_session.commit()

    db_session.refresh(user)

    response = client.get(f"/api/users/{user.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)

    assert data["username"] == "getuser"


def test_get_user_not_found():

    response = client.get(f"/api/users/{uuid4()}")

    assert response.status_code == 404


def test_list_users(db_session: Session):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    for i in range(3):

        db_session.add(
            User(
                username=f"user{i}",
                email=f"user{i}@test.com",
                password_hash="hash",
                first_name="User",
            )
        )

    db_session.commit()

    response = client.get("/api/users/")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3

    assert len(data["data"]) == 3

    assert data["page"] == 1

    assert data["size"] == 10


def test_list_users_with_pagination(db_session: Session):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    for i in range(15):

        db_session.add(
            User(
                username=f"user{i}",
                email=f"user{i}@test.com",
                password_hash="hash",
                first_name="User",
            )
        )

    db_session.commit()

    response = client.get("/api/users/?page=2&size=5")

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2

    assert data["size"] == 5

    assert len(data["data"]) == 5


def test_update_user(db_session: Session):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    user = User(
        username="updateuser",
        email="update@test.com",
        password_hash="hash",
        first_name="Old",
    )

    db_session.add(user)

    db_session.commit()

    db_session.refresh(user)

    response = client.put(
        f"/api/users/{user.id}", json={"first_name": "New", "designation": "Manager"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "New"

    assert data["designation"] == "Manager"


def test_update_user_not_found():

    response = client.put(f"/api/users/{uuid4()}", json={"first_name": "New"})

    assert response.status_code == 404


def test_delete_user(db_session: Session):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    user = User(
        username="deleteuser",
        email="delete@test.com",
        password_hash="hash",
        first_name="Delete",
    )

    db_session.add(user)

    db_session.commit()

    db_session.refresh(user)

    response = client.delete(f"/api/users/{user.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["message"] == "User deleted successfully."

    deleted_user = db_session.query(User).filter(User.id == user.id).first()

    assert deleted_user.is_deleted is True


def test_delete_user_not_found():

    response = client.delete(f"/api/users/{uuid4()}")

    assert response.status_code == 404


def test_get_users_by_organization_api(db_session: Session):

    app.dependency_overrides[get_db] = override_get_db(db_session)

    from app.organizations.models import Organization
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    org = Organization(name="Test Org Router")
    role = Role(name="Member Role Router", description="Member Router")
    user = User(
        username="orguser",
        email="orguser@test.com",
        password_hash="hash",
        first_name="OrgUser",
    )
    db_session.add_all([org, role, user])
    db_session.commit()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(member)
    db_session.commit()

    response = client.get(f"/api/users/organization/{org.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["username"] == "orguser"


def test_get_users_me_super_admin(db_session: Session):
    app.dependency_overrides[get_db] = override_get_db(db_session)
    from app.organizations.models import Organization
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    org = Organization(id=uuid4(), name="SSDN TECHNOLOGIES")
    role = Role(id=uuid4(), name="SUPER_ADMIN", description="System administrator")
    user = User(
        id=uuid4(),
        username="superadmin_test",
        email="superadmin@test.com",
        password_hash="hash",
        first_name="Super",
        last_name="Admin",
    )
    db_session.add_all([org, role, user])
    db_session.commit()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()

    assert "role" not in data
    assert data["username"] == "superadmin_test"
    assert "organization_memberships" in data
    assert len(data["organization_memberships"]) == 1
    membership = data["organization_memberships"][0]
    assert membership["organization_id"] == str(org.id)
    assert membership["organization_name"] == "SSDN TECHNOLOGIES"
    assert membership["role"]["name"] == "SUPER_ADMIN"
    assert membership["batch_id"] is None


def test_get_users_me_employee(db_session: Session):
    app.dependency_overrides[get_db] = override_get_db(db_session)
    from app.organizations.models import Organization
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    org = Organization(id=uuid4(), name="Acme Corp")
    role = Role(id=uuid4(), name="EMPLOYEE", description="Regular employee")
    user = User(
        id=uuid4(),
        username="employee_test",
        email="employee@test.com",
        password_hash="hash",
        first_name="John",
    )
    db_session.add_all([org, role, user])
    db_session.commit()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()

    assert "role" not in data
    assert data["username"] == "employee_test"
    assert len(data["organization_memberships"]) == 1
    membership = data["organization_memberships"][0]
    assert membership["organization_id"] == str(org.id)
    assert membership["organization_name"] == "Acme Corp"
    assert membership["role"]["name"] == "EMPLOYEE"


def test_get_users_me_multiple_memberships(db_session: Session):
    app.dependency_overrides[get_db] = override_get_db(db_session)
    from app.organizations.models import Organization
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    org_a = Organization(id=uuid4(), name="Organization A")
    org_b = Organization(id=uuid4(), name="Organization B")
    role_admin = Role(id=uuid4(), name="ORG_ADMIN", description="Org Admin")
    role_emp = Role(id=uuid4(), name="EMPLOYEE", description="Employee")
    user = User(
        id=uuid4(),
        username="multi_org_test",
        email="multi@test.com",
        password_hash="hash",
        first_name="Multi",
    )
    db_session.add_all([org_a, org_b, role_admin, role_emp, user])
    db_session.commit()

    m1 = OrganizationMember(organization_id=org_a.id, user_id=user.id, role_id=role_admin.id)
    m2 = OrganizationMember(organization_id=org_b.id, user_id=user.id, role_id=role_emp.id)
    db_session.add_all([m1, m2])
    db_session.commit()
    db_session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user

    # No X-Organization-ID header supplied
    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()

    assert "role" not in data
    assert len(data["organization_memberships"]) == 2
    org_names = {m["organization_name"] for m in data["organization_memberships"]}
    assert org_names == {"Organization A", "Organization B"}


def test_get_users_me_no_memberships(db_session: Session):
    app.dependency_overrides[get_db] = override_get_db(db_session)

    user = User(
        id=uuid4(),
        username="no_member_test",
        email="nomember@test.com",
        password_hash="hash",
        first_name="NoMember",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()

    assert "role" not in data
    assert "organization_memberships" in data
    assert data["organization_memberships"] == []


def test_get_users_me_deduplicates_same_org(db_session: Session):
    app.dependency_overrides[get_db] = override_get_db(db_session)
    from app.organizations.models import Organization
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    org = Organization(id=uuid4(), name="Deduplication Org")
    role_old = Role(id=uuid4(), name="EMPLOYEE", description="Old Role")
    role_new = Role(id=uuid4(), name="ORG_ADMIN", description="New Role")
    user = User(
        id=uuid4(),
        username="dedup_test",
        email="dedup@test.com",
        password_hash="hash",
        first_name="Dedup",
    )
    db_session.add_all([org, role_old, role_new, user])
    db_session.commit()

    m_old = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=role_old.id,
    )
    db_session.add(m_old)
    db_session.commit()

    m_new = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=role_new.id,
    )
    # Even if duplicate legacy rows exist in Python list
    user.organization_members = [m_old, m_new]

    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()

    assert "role" not in data
    assert len(data["organization_memberships"]) == 1
    assert data["organization_memberships"][0]["organization_id"] == str(org.id)


def test_list_users_detailed_structure(db_session: Session, test_org, test_role):
    """
    Verify GET /api/users/ returns the same detailed structure as GET /api/users/{user_id}.
    """
    app.dependency_overrides[get_db] = override_get_db(db_session)

    payload = create_payload(test_org.id, test_role.id)
    payload["phone"] = "9876543210"
    payload["description"] = "Senior Engineer"
    payload["designation"] = "Lead"

    create_res = client.post("/api/users/", json=payload)
    assert create_res.status_code == 201

    response = client.get("/api/users/?page=1&size=10&sort_by=created_at&sort_order=desc")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert data["page"] == 1
    assert data["size"] == 10
    assert data["total"] >= 1

    matched = [u for u in data["data"] if u["username"] == "testuser"]
    assert len(matched) == 1
    user_item = matched[0]

    # Verify user scalar fields
    assert user_item["username"] == "testuser"
    assert user_item["phone"] == "9876543210"
    assert user_item["description"] == "Senior Engineer"
    assert user_item["designation"] == "Lead"
    assert user_item["is_active"] is True
    assert "created_at" in user_item and user_item["created_at"] is not None
    assert "updated_at" in user_item and user_item["updated_at"] is not None
    assert "role" not in user_item

    # Verify organization memberships structure
    assert "organization_memberships" in user_item
    assert len(user_item["organization_memberships"]) >= 1
    membership = user_item["organization_memberships"][0]
    assert membership["organization_id"] == str(test_org.id)
    assert membership["organization_name"] == test_org.name
    assert membership["batch_id"] is None
    assert membership["role"]["id"] == str(test_role.id)
    assert membership["role"]["name"] == test_role.name
    assert "description" in membership["role"]





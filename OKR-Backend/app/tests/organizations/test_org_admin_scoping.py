import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.core.database import get_db
from app.main import app
from app.organizations.models import Organization
from app.organization_members.models import OrganizationMember
from app.rbac.models import Role
from app.rbac.policies import RoleCode
from app.users.models import User


def get_auth_headers(user: User, org_id: uuid.UUID | None = None) -> dict:
    token = create_access_token({"sub": str(user.id), "email": user.email})
    headers = {"Authorization": f"Bearer {token}"}
    if org_id:
        headers["X-Organization-ID"] = str(org_id)
    return headers


@pytest.fixture
def multi_org_setup(db_session: Session):
    # 2 Organizations
    org_a = Organization(id=uuid.uuid4(), name="Org Alpha", is_deleted=False)
    org_b = Organization(id=uuid.uuid4(), name="Org Beta", is_deleted=False)
    db_session.add_all([org_a, org_b])
    db_session.flush()

    # Roles
    role_org_admin = (
        db_session.query(Role).filter(Role.name == RoleCode.ORG_ADMIN.value).first()
        or Role(id=uuid.uuid4(), name=RoleCode.ORG_ADMIN.value, description="Org Admin")
    )
    role_emp = (
        db_session.query(Role).filter(Role.name == RoleCode.EMPLOYEE.value).first()
        or Role(id=uuid.uuid4(), name=RoleCode.EMPLOYEE.value, description="Employee")
    )
    db_session.add_all([role_org_admin, role_emp])
    db_session.flush()

    # Users
    user_org_admin = User(
        id=uuid.uuid4(),
        username="org_admin_alpha",
        email="admin@alpha.com",
        password_hash=hash_password("Pass123!"),
        first_name="Admin",
        is_deleted=False,
        is_active=True,
    )
    user_emp_a = User(
        id=uuid.uuid4(),
        username="emp_alpha",
        email="emp@alpha.com",
        password_hash=hash_password("Pass123!"),
        first_name="EmpA",
        is_deleted=False,
        is_active=True,
    )
    user_emp_b = User(
        id=uuid.uuid4(),
        username="emp_beta",
        email="emp@beta.com",
        password_hash=hash_password("Pass123!"),
        first_name="EmpB",
        is_deleted=False,
        is_active=True,
    )
    db_session.add_all([user_org_admin, user_emp_a, user_emp_b])
    db_session.flush()

    # Memberships
    m_admin = OrganizationMember(
        organization_id=org_a.id,
        user_id=user_org_admin.id,
        role_id=role_org_admin.id,
        is_deleted=False,
        is_active=True,
    )
    m_emp_a = OrganizationMember(
        organization_id=org_a.id,
        user_id=user_emp_a.id,
        role_id=role_emp.id,
        is_deleted=False,
        is_active=True,
    )
    m_emp_b = OrganizationMember(
        organization_id=org_b.id,
        user_id=user_emp_b.id,
        role_id=role_emp.id,
        is_deleted=False,
        is_active=True,
    )
    db_session.add_all([m_admin, m_emp_a, m_emp_b])
    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "admin": user_org_admin,
        "emp_a": user_emp_a,
        "emp_b": user_emp_b,
    }


def test_org_admin_lists_only_own_organization(auth_jwt_client: TestClient, multi_org_setup):
    headers = get_auth_headers(multi_org_setup["admin"])
    response = auth_jwt_client.get("/api/organizations/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    org_ids = [org["id"] for org in data["data"]]
    assert str(multi_org_setup["org_a"].id) in org_ids
    assert str(multi_org_setup["org_b"].id) not in org_ids
    assert data["pagination"]["total"] == 1


def test_org_admin_cannot_get_foreign_organization(auth_jwt_client: TestClient, multi_org_setup):
    headers = get_auth_headers(multi_org_setup["admin"])
    foreign_id = multi_org_setup["org_b"].id
    response = auth_jwt_client.get(f"/api/organizations/{foreign_id}", headers=headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_org_admin_can_get_own_organization(auth_jwt_client: TestClient, multi_org_setup):
    headers = get_auth_headers(multi_org_setup["admin"])
    own_id = multi_org_setup["org_a"].id
    response = auth_jwt_client.get(f"/api/organizations/{own_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(own_id)


def test_org_admin_users_list_strictly_scoped_to_own_organization(auth_jwt_client: TestClient, multi_org_setup):
    headers = get_auth_headers(multi_org_setup["admin"])
    response = auth_jwt_client.get("/api/users/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    user_ids = [u["id"] for u in data["data"]]
    assert str(multi_org_setup["admin"].id) in user_ids
    assert str(multi_org_setup["emp_a"].id) in user_ids
    assert str(multi_org_setup["emp_b"].id) not in user_ids


def test_org_admin_users_list_rejects_foreign_org_header(auth_jwt_client: TestClient, multi_org_setup):
    headers = get_auth_headers(multi_org_setup["admin"], multi_org_setup["org_b"].id)
    response = auth_jwt_client.get("/api/users/", headers=headers)
    assert response.status_code == 403
    assert "not an active member" in response.json()["detail"]

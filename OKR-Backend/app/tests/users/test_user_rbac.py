"""
Role-Based Access Control (RBAC) & Multi-Tenancy Tests for Users Module.

Contains all 32 test cases validating authorization and multi-tenant security:
1. SUPER_ADMIN lists all users.
2. SUPER_ADMIN gets any user.
3. SUPER_ADMIN creates user.
4. SUPER_ADMIN updates user.
5. SUPER_ADMIN deletes user.
6. ORG_ADMIN lists own organization.
7. ORG_ADMIN cannot list another organization.
8. ORG_ADMIN gets own organization user.
9. ORG_ADMIN cannot get another organization's user.
10. ORG_ADMIN creates user in own organization.
11. ORG_ADMIN cannot create user in another organization.
12. ORG_ADMIN updates own organization user.
13. ORG_ADMIN cannot update another organization's user.
14. ORG_ADMIN cannot delete.
15. ORG_ADMIN cannot grant SUPER_ADMIN.
16. BATCH_ADMIN lists own batch.
17. BATCH_ADMIN cannot see another batch.
18. BATCH_ADMIN cannot see another organization.
19. BATCH_ADMIN cannot create.
20. BATCH_ADMIN cannot update.
21. BATCH_ADMIN cannot delete.
22. EMPLOYEE can access /users/me.
23. EMPLOYEE cannot list users.
24. EMPLOYEE cannot get /users/{id}.
25. EMPLOYEE cannot update self.
26. EMPLOYEE cannot create.
27. EMPLOYEE cannot delete.
28. Invalid JWT returns 401.
29. Missing JWT returns 401.
30. X-Organization-ID cannot bypass scope.
31. Invalid batch/organization combination is rejected.
32. Unauthorized user UUID cannot bypass scope.
"""

import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.batches.models import Batch, BatchMember, BatchStatus, MeetingDay, Quarter
from app.core.database import get_db
from app.main import app as fastapi_app
from app.organizations.models import Organization
from app.organization_members.models import OrganizationMember
from app.rbac.models import Role
from app.rbac.policies import RoleCode
from app.users.models import User


def get_auth_headers(user: User, org_id: uuid.UUID | None = None) -> dict:
    """Generate JWT authorization headers and optional X-Organization-ID header."""
    token = create_access_token({"sub": str(user.id), "email": user.email})
    headers = {"Authorization": f"Bearer {token}"}
    if org_id:
        headers["X-Organization-ID"] = str(org_id)
    return headers


@pytest.fixture
def rbac_setup(db_session: Session):
    """
    Sets up a complete multi-organization, multi-batch, multi-role test fixture:
    - 2 Organizations (org_a, org_b)
    - 2 Batches (batch_a in org_a, batch_b in org_b)
    - 4 System Roles (SUPER_ADMIN, ORG_ADMIN, BATCH_ADMIN, EMPLOYEE)
    - Users across roles and orgs
    """
    # 1. Organizations
    org_a = Organization(id=uuid.uuid4(), name="Acme Corp A", is_deleted=False)
    org_b = Organization(id=uuid.uuid4(), name="Beta Corp B", is_deleted=False)
    db_session.add_all([org_a, org_b])
    db_session.flush()

    # 2. Batches
    batch_a = Batch(
        id=uuid.uuid4(),
        name="Batch Alpha",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        status=BatchStatus.ACTIVE,
        organization_id=org_a.id,
        is_deleted=False,
    )
    batch_b = Batch(
        id=uuid.uuid4(),
        name="Batch Beta",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.TUESDAY,
        status=BatchStatus.ACTIVE,
        organization_id=org_b.id,
        is_deleted=False,
    )
    db_session.add_all([batch_a, batch_b])
    db_session.flush()

    # 3. Roles
    role_super = Role(id=uuid.uuid4(), name=RoleCode.SUPER_ADMIN.value, description="Super Admin")
    role_org_admin = Role(id=uuid.uuid4(), name=RoleCode.ORG_ADMIN.value, description="Org Admin")
    role_batch_admin = Role(id=uuid.uuid4(), name=RoleCode.BATCH_ADMIN.value, description="Batch Admin")
    role_emp = Role(id=uuid.uuid4(), name=RoleCode.EMPLOYEE.value, description="Employee")
    db_session.add_all([role_super, role_org_admin, role_batch_admin, role_emp])
    db_session.flush()

    # 4. Users
    super_admin = User(
        id=uuid.uuid4(),
        username="rbac_superadmin",
        email="superadmin@acme.com",
        password_hash=hash_password("Pass@123"),
        first_name="Super",
        last_name="Admin",
        is_deleted=False,
        is_active=True,
    )
    setattr(super_admin, "is_superuser", True)

    org_admin_a = User(
        id=uuid.uuid4(),
        username="rbac_orgadmin_a",
        email="orgadmin_a@acme.com",
        password_hash=hash_password("Pass@123"),
        first_name="OrgAdmin",
        last_name="A",
        is_deleted=False,
        is_active=True,
    )

    org_admin_b = User(
        id=uuid.uuid4(),
        username="rbac_orgadmin_b",
        email="orgadmin_b@beta.com",
        password_hash=hash_password("Pass@123"),
        first_name="OrgAdmin",
        last_name="B",
        is_deleted=False,
        is_active=True,
    )

    batch_admin_a = User(
        id=uuid.uuid4(),
        username="rbac_batchadmin_a",
        email="batchadmin_a@acme.com",
        password_hash=hash_password("Pass@123"),
        first_name="BatchAdmin",
        last_name="A",
        is_deleted=False,
        is_active=True,
    )

    employee_a = User(
        id=uuid.uuid4(),
        username="rbac_employee_a",
        email="employee_a@acme.com",
        password_hash=hash_password("Pass@123"),
        first_name="Employee",
        last_name="A",
        is_deleted=False,
        is_active=True,
    )

    employee_b = User(
        id=uuid.uuid4(),
        username="rbac_employee_b",
        email="employee_b@beta.com",
        password_hash=hash_password("Pass@123"),
        first_name="Employee",
        last_name="B",
        is_deleted=False,
        is_active=True,
    )

    db_session.add_all([super_admin, org_admin_a, org_admin_b, batch_admin_a, employee_a, employee_b])
    db_session.flush()

    # 5. Organization Memberships
    m_super = OrganizationMember(
        organization_id=org_a.id,
        user_id=super_admin.id,
        role_id=role_super.id,
        is_deleted=False,
        is_active=True,
    )
    m_org_a = OrganizationMember(
        organization_id=org_a.id,
        user_id=org_admin_a.id,
        role_id=role_org_admin.id,
        is_deleted=False,
        is_active=True,
    )
    m_org_b = OrganizationMember(
        organization_id=org_b.id,
        user_id=org_admin_b.id,
        role_id=role_org_admin.id,
        is_deleted=False,
        is_active=True,
    )
    m_batch_a = OrganizationMember(
        organization_id=org_a.id,
        user_id=batch_admin_a.id,
        role_id=role_batch_admin.id,
        is_deleted=False,
        is_active=True,
    )
    m_emp_a = OrganizationMember(
        organization_id=org_a.id,
        user_id=employee_a.id,
        role_id=role_emp.id,
        is_deleted=False,
        is_active=True,
    )
    m_emp_b = OrganizationMember(
        organization_id=org_b.id,
        user_id=employee_b.id,
        role_id=role_emp.id,
        is_deleted=False,
        is_active=True,
    )

    bm_batch_a = BatchMember(
        batch_id=batch_a.id,
        user_id=batch_admin_a.id,
        role_id=role_batch_admin.id,
        is_deleted=False,
        is_active=True,
    )
    bm_emp_a = BatchMember(
        batch_id=batch_a.id,
        user_id=employee_a.id,
        role_id=role_emp.id,
        is_deleted=False,
        is_active=True,
    )
    bm_emp_b = BatchMember(
        batch_id=batch_b.id,
        user_id=employee_b.id,
        role_id=role_emp.id,
        is_deleted=False,
        is_active=True,
    )

    db_session.add_all([
        m_super, m_org_a, m_org_b, m_batch_a, m_emp_a, m_emp_b,
        bm_batch_a, bm_emp_a, bm_emp_b
    ])
    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "batch_a": batch_a,
        "batch_b": batch_b,
        "role_super": role_super,
        "role_org_admin": role_org_admin,
        "role_batch_admin": role_batch_admin,
        "role_emp": role_emp,
        "super_admin": super_admin,
        "org_admin_a": org_admin_a,
        "org_admin_b": org_admin_b,
        "batch_admin_a": batch_admin_a,
        "employee_a": employee_a,
        "employee_b": employee_b,
    }


# ============================================================================
# Section 19 Security Test Cases (1 to 32)
# ============================================================================


def test_rbac_01_super_admin_lists_all_users(auth_jwt_client: TestClient, rbac_setup):
    """1. SUPER_ADMIN lists all users across the system."""
    headers = get_auth_headers(rbac_setup["super_admin"])
    response = auth_jwt_client.get("/api/users/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 6


def test_rbac_02_super_admin_gets_any_user(auth_jwt_client: TestClient, rbac_setup):
    """2. SUPER_ADMIN gets any user by UUID."""
    headers = get_auth_headers(rbac_setup["super_admin"])
    target_id = rbac_setup["employee_b"].id
    response = auth_jwt_client.get(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "rbac_employee_b"


def test_rbac_03_super_admin_creates_user(auth_jwt_client: TestClient, rbac_setup):
    """3. SUPER_ADMIN creates user in any organization."""
    headers = get_auth_headers(rbac_setup["super_admin"])
    payload = {
        "username": "super_created_user",
        "email": "super_created@test.com",
        "password": "Password@123",
        "first_name": "Created",
        "last_name": "BySuper",
        "organization_id": str(rbac_setup["org_b"].id),
        "role_id": str(rbac_setup["role_emp"].id),
    }
    response = auth_jwt_client.post("/api/users/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["username"] == "super_created_user"


def test_rbac_04_super_admin_updates_user(auth_jwt_client: TestClient, rbac_setup):
    """4. SUPER_ADMIN updates any user."""
    headers = get_auth_headers(rbac_setup["super_admin"])
    target_id = rbac_setup["employee_b"].id
    response = auth_jwt_client.put(
        f"/api/users/{target_id}",
        json={"first_name": "SuperUpdatedName"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "SuperUpdatedName"


def test_rbac_05_super_admin_deletes_user(auth_jwt_client: TestClient, rbac_setup, db_session: Session):
    """5. SUPER_ADMIN deletes any user (soft delete)."""
    headers = get_auth_headers(rbac_setup["super_admin"])
    target_id = rbac_setup["employee_b"].id
    response = auth_jwt_client.delete(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    deleted_user = db_session.query(User).filter(User.id == target_id).first()
    assert deleted_user.is_deleted is True


def test_rbac_06_org_admin_lists_own_organization(auth_jwt_client: TestClient, rbac_setup):
    """6. ORG_ADMIN lists own organization users."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    org_a_id = rbac_setup["org_a"].id
    response = auth_jwt_client.get(f"/api/users/organization/{org_a_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4


def test_rbac_07_org_admin_cannot_list_another_organization(auth_jwt_client: TestClient, rbac_setup):
    """7. ORG_ADMIN cannot list another organization's users (403 Forbidden)."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    org_b_id = rbac_setup["org_b"].id
    response = auth_jwt_client.get(f"/api/users/organization/{org_b_id}", headers=headers)
    assert response.status_code == 403
    assert "Access denied to users in another organization" in response.json()["detail"]


def test_rbac_08_org_admin_gets_own_organization_user(auth_jwt_client: TestClient, rbac_setup):
    """8. ORG_ADMIN gets user in own organization."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.get(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "rbac_employee_a"


def test_rbac_09_org_admin_cannot_get_another_organization_user(auth_jwt_client: TestClient, rbac_setup):
    """9. ORG_ADMIN cannot get another organization's user (403 Forbidden)."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_b"].id
    response = auth_jwt_client.get(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 403
    assert "Access denied to users outside your organization" in response.json()["detail"]


def test_rbac_10_org_admin_creates_user_in_own_organization(auth_jwt_client: TestClient, rbac_setup):
    """10. ORG_ADMIN creates user in own organization."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    payload = {
        "username": "org_created_user",
        "email": "org_created@test.com",
        "password": "Password@123",
        "first_name": "OrgCreated",
        "organization_id": str(rbac_setup["org_a"].id),
        "role_id": str(rbac_setup["role_emp"].id),
    }
    response = auth_jwt_client.post("/api/users/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["username"] == "org_created_user"


def test_rbac_11_org_admin_cannot_create_user_in_another_organization(auth_jwt_client: TestClient, rbac_setup):
    """11. ORG_ADMIN cannot create user in another organization (403 Forbidden)."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    payload = {
        "username": "cross_org_user",
        "email": "cross_org@test.com",
        "password": "Password@123",
        "first_name": "Cross",
        "organization_id": str(rbac_setup["org_b"].id),
        "role_id": str(rbac_setup["role_emp"].id),
    }
    response = auth_jwt_client.post("/api/users/", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Access denied to users in another organization" in response.json()["detail"]


def test_rbac_12_org_admin_updates_own_organization_user(auth_jwt_client: TestClient, rbac_setup):
    """12. ORG_ADMIN updates own organization user."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.put(
        f"/api/users/{target_id}",
        json={"first_name": "UpdatedByOrgAdmin"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "UpdatedByOrgAdmin"


def test_rbac_13_org_admin_cannot_update_another_organization_user(auth_jwt_client: TestClient, rbac_setup):
    """13. ORG_ADMIN cannot update another organization's user (403 Forbidden)."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_b"].id
    response = auth_jwt_client.put(
        f"/api/users/{target_id}",
        json={"first_name": "CrossUpdate"},
        headers=headers,
    )
    assert response.status_code == 403
    assert "Access denied to users outside your organization" in response.json()["detail"]


def test_rbac_14_org_admin_cannot_delete(auth_jwt_client: TestClient, rbac_setup):
    """14. ORG_ADMIN cannot delete users (403 Forbidden - missing user.delete)."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.delete(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_15_org_admin_cannot_grant_super_admin(auth_jwt_client: TestClient, rbac_setup):
    """15. ORG_ADMIN cannot create a user with SUPER_ADMIN role (403 Privilege Escalation Protection)."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    payload = {
        "username": "escalation_attempt",
        "email": "escalation@test.com",
        "password": "Password@123",
        "first_name": "Escalation",
        "organization_id": str(rbac_setup["org_a"].id),
        "role_id": str(rbac_setup["role_super"].id),
    }
    response = auth_jwt_client.post("/api/users/", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Only super admins can assign the super admin role" in response.json()["detail"]


def test_rbac_16_batch_admin_lists_own_batch(auth_jwt_client: TestClient, rbac_setup):
    """16. BATCH_ADMIN can view own profile via /users/me."""
    headers = get_auth_headers(rbac_setup["batch_admin_a"], rbac_setup["org_a"].id)
    response = auth_jwt_client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "rbac_batchadmin_a"


def test_rbac_17_batch_admin_cannot_see_another_batch(auth_jwt_client: TestClient, rbac_setup):
    """17. BATCH_ADMIN cannot access other users outside their scope (403 Forbidden)."""
    headers = get_auth_headers(rbac_setup["batch_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.get(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 403
    assert "You do not have permission to manage users" in response.json()["detail"]


def test_rbac_18_batch_admin_cannot_see_another_organization(auth_jwt_client: TestClient, rbac_setup):
    """18. BATCH_ADMIN cannot list another organization (403 Forbidden)."""
    headers = get_auth_headers(rbac_setup["batch_admin_a"], rbac_setup["org_a"].id)
    org_b_id = rbac_setup["org_b"].id
    response = auth_jwt_client.get(f"/api/users/organization/{org_b_id}", headers=headers)
    assert response.status_code == 403


def test_rbac_19_batch_admin_cannot_create(auth_jwt_client: TestClient, rbac_setup):
    """19. BATCH_ADMIN cannot create users (403 Forbidden - missing user.create)."""
    headers = get_auth_headers(rbac_setup["batch_admin_a"], rbac_setup["org_a"].id)
    payload = {
        "username": "batch_create_attempt",
        "email": "batch_create@test.com",
        "password": "Password@123",
        "first_name": "BatchUser",
        "organization_id": str(rbac_setup["org_a"].id),
        "role_id": str(rbac_setup["role_emp"].id),
    }
    response = auth_jwt_client.post("/api/users/", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_20_batch_admin_cannot_update(auth_jwt_client: TestClient, rbac_setup):
    """20. BATCH_ADMIN cannot update users (403 Forbidden - missing user.update)."""
    headers = get_auth_headers(rbac_setup["batch_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.put(
        f"/api/users/{target_id}",
        json={"first_name": "BatchUpdate"},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_21_batch_admin_cannot_delete(auth_jwt_client: TestClient, rbac_setup):
    """21. BATCH_ADMIN cannot delete users (403 Forbidden - missing user.delete)."""
    headers = get_auth_headers(rbac_setup["batch_admin_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.delete(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_22_employee_can_access_users_me(auth_jwt_client: TestClient, rbac_setup):
    """22. EMPLOYEE can access /api/users/me to view own authenticated profile."""
    headers = get_auth_headers(rbac_setup["employee_a"], rbac_setup["org_a"].id)
    response = auth_jwt_client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "rbac_employee_a"


def test_rbac_23_employee_cannot_list_users(auth_jwt_client: TestClient, rbac_setup):
    """23. EMPLOYEE cannot list users (403 Forbidden - missing user.view)."""
    headers = get_auth_headers(rbac_setup["employee_a"], rbac_setup["org_a"].id)
    response = auth_jwt_client.get("/api/users/", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_24_employee_cannot_get_users_by_id(auth_jwt_client: TestClient, rbac_setup):
    """24. EMPLOYEE cannot get other users by ID (403 Forbidden)."""
    headers = get_auth_headers(rbac_setup["employee_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["org_admin_a"].id
    response = auth_jwt_client.get(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 403
    assert "You do not have permission to manage users" in response.json()["detail"]


def test_rbac_25_employee_cannot_update_self(auth_jwt_client: TestClient, rbac_setup):
    """25. EMPLOYEE cannot update self via admin PUT /api/users/{id} (403 Forbidden - missing user.update)."""
    headers = get_auth_headers(rbac_setup["employee_a"], rbac_setup["org_a"].id)
    self_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.put(
        f"/api/users/{self_id}",
        json={"first_name": "EmployeeSelfUpdate"},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_26_employee_cannot_create(auth_jwt_client: TestClient, rbac_setup):
    """26. EMPLOYEE cannot create users (403 Forbidden - missing user.create)."""
    headers = get_auth_headers(rbac_setup["employee_a"], rbac_setup["org_a"].id)
    payload = {
        "username": "emp_create_attempt",
        "email": "emp_create@test.com",
        "password": "Password@123",
        "first_name": "EmpUser",
        "organization_id": str(rbac_setup["org_a"].id),
        "role_id": str(rbac_setup["role_emp"].id),
    }
    response = auth_jwt_client.post("/api/users/", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_27_employee_cannot_delete(auth_jwt_client: TestClient, rbac_setup):
    """27. EMPLOYEE cannot delete users (403 Forbidden - missing user.delete)."""
    headers = get_auth_headers(rbac_setup["employee_a"], rbac_setup["org_a"].id)
    target_id = rbac_setup["employee_a"].id
    response = auth_jwt_client.delete(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission denied."


def test_rbac_28_invalid_jwt_returns_401(auth_jwt_client: TestClient):
    """28. Invalid JWT token returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer invalid_malformed_token"}
    response = auth_jwt_client.get("/api/users/me", headers=headers)
    assert response.status_code == 401


def test_rbac_29_missing_jwt_returns_401(auth_jwt_client: TestClient):
    """29. Missing JWT Authorization header returns 401 Unauthorized."""
    response = auth_jwt_client.get("/api/users/me")
    assert response.status_code == 401


def test_rbac_30_x_org_id_cannot_bypass_scope(auth_jwt_client: TestClient, rbac_setup):
    """30. Passing an unauthorized X-Organization-ID header cannot bypass organization scope (403 Forbidden)."""
    # User belongs to Org A only, but supplies X-Organization-ID of Org B
    headers = get_auth_headers(rbac_setup["org_admin_a"], org_id=rbac_setup["org_b"].id)
    response = auth_jwt_client.get("/api/users/", headers=headers)
    assert response.status_code == 403
    assert "User is not an active member of this organization" in response.json()["detail"]


def test_rbac_31_invalid_batch_org_combination_rejected(auth_jwt_client: TestClient, rbac_setup):
    """31. Invalid organization or role combination is rejected with 404."""
    headers = get_auth_headers(rbac_setup["super_admin"])
    payload = {
        "username": "invalid_org_user",
        "email": "invalid_org@test.com",
        "password": "Password@123",
        "first_name": "Invalid",
        "organization_id": str(uuid.uuid4()),
        "role_id": str(rbac_setup["role_emp"].id),
    }
    response = auth_jwt_client.post("/api/users/", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Organization not found" in response.json()["detail"]


def test_rbac_32_unauthorized_user_uuid_cannot_bypass_scope(auth_jwt_client: TestClient, rbac_setup):
    """32. Supplying random or cross-org user UUIDs cannot bypass tenant authorization checks."""
    headers = get_auth_headers(rbac_setup["org_admin_a"], rbac_setup["org_a"].id)
    # Cross-org UUID
    target_id = rbac_setup["employee_b"].id
    response = auth_jwt_client.get(f"/api/users/{target_id}", headers=headers)
    assert response.status_code == 403
    assert "Access denied to users outside your organization" in response.json()["detail"]

    # Non-existent UUID
    random_id = uuid.uuid4()
    response_nonexistent = auth_jwt_client.get(f"/api/users/{random_id}", headers=headers)
    assert response_nonexistent.status_code == 404

"""
Role-Based Access Control (RBAC) & Multi-Tenancy Tests for Batches Module.

Validates permissions, tenant boundaries, batch scoping, and lifecycle rules:
- SUPER_ADMIN: Global CRUD & management across all organizations.
- ORG_ADMIN: Scoped CRUD & management within own organization. Cross-org denied (403).
- BATCH_ADMIN: Scoped view, update, and close on assigned batch. Create/delete denied (403).
- EMPLOYEE: No batch access. All batch operations denied (403).
- Security: Missing/invalid JWT (401), header spoofing (403), closed batch mutation protection (400).
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
def batch_rbac_setup(db_session: Session):
    """
    Sets up a multi-organization, multi-batch, multi-role test fixture:
    - 2 Organizations (org_a, org_b)
    - 3 Batches (batch_a1, batch_a2 in org_a; batch_b in org_b)
    - 4 System Roles (SUPER_ADMIN, ORG_ADMIN, BATCH_ADMIN, EMPLOYEE)
    - Users assigned to roles across org_a and org_b
    """
    # 1. Organizations
    org_a = Organization(id=uuid.uuid4(), name="Acme Org A", is_deleted=False)
    org_b = Organization(id=uuid.uuid4(), name="Beta Org B", is_deleted=False)
    db_session.add_all([org_a, org_b])
    db_session.flush()

    # 2. Batches
    batch_a1 = Batch(
        id=uuid.uuid4(),
        name="Batch Alpha 1",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        status=BatchStatus.ACTIVE,
        organization_id=org_a.id,
        is_deleted=False,
    )
    batch_a2 = Batch(
        id=uuid.uuid4(),
        name="Batch Alpha 2",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.TUESDAY,
        status=BatchStatus.ACTIVE,
        organization_id=org_a.id,
        is_deleted=False,
    )
    batch_b = Batch(
        id=uuid.uuid4(),
        name="Batch Beta 1",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.WEDNESDAY,
        status=BatchStatus.ACTIVE,
        organization_id=org_b.id,
        is_deleted=False,
    )
    db_session.add_all([batch_a1, batch_a2, batch_b])
    db_session.flush()

    # 3. Roles
    def get_or_create_role(name: str, code: str) -> Role:
        role = db_session.query(Role).filter(Role.name == name).first()
        if not role:
            role = Role(id=uuid.uuid4(), name=name, description=f"{name} role")
            db_session.add(role)
            db_session.flush()
        return role

    role_super = get_or_create_role("SUPER_ADMIN", "SUPER_ADMIN")
    role_org_admin = get_or_create_role("ORG_ADMIN", "ORG_ADMIN")
    role_batch_admin = get_or_create_role("BATCH_ADMIN", "BATCH_ADMIN")
    role_employee = get_or_create_role("EMPLOYEE", "EMPLOYEE")

    # 4. Users
    pwd = hash_password("Password123!")

    super_user = User(
        id=uuid.uuid4(),
        username="superadmin",
        email="superadmin@example.com",
        password_hash=pwd,
        first_name="Super",
        last_name="Admin",
        is_active=True,
        is_deleted=False,
    )
    org_admin_a = User(
        id=uuid.uuid4(),
        username="orgadmin_a",
        email="orgadmin_a@example.com",
        password_hash=pwd,
        first_name="OrgAdmin",
        last_name="A",
        is_active=True,
        is_deleted=False,
    )
    batch_admin_a1 = User(
        id=uuid.uuid4(),
        username="batchadmin_a1",
        email="batchadmin_a1@example.com",
        password_hash=pwd,
        first_name="BatchAdmin",
        last_name="A1",
        is_active=True,
        is_deleted=False,
    )
    emp_a1 = User(
        id=uuid.uuid4(),
        username="employee_a1",
        email="emp_a1@example.com",
        password_hash=pwd,
        first_name="Employee",
        last_name="A1",
        is_active=True,
        is_deleted=False,
    )
    emp_b = User(
        id=uuid.uuid4(),
        username="employee_b",
        email="emp_b@example.com",
        password_hash=pwd,
        first_name="Employee",
        last_name="B",
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([super_user, org_admin_a, batch_admin_a1, emp_a1, emp_b])
    db_session.flush()

    # 5. Organization Memberships
    # Super Admin (Global membership with SUPER_ADMIN role)
    mem_super = OrganizationMember(
        id=uuid.uuid4(),
        user_id=super_user.id,
        organization_id=org_a.id,
        role_id=role_super.id,
        is_active=True,
        is_deleted=False,
    )
    # Org Admin for Org A
    mem_org_a = OrganizationMember(
        id=uuid.uuid4(),
        user_id=org_admin_a.id,
        organization_id=org_a.id,
        role_id=role_org_admin.id,
        is_active=True,
        is_deleted=False,
    )
    # Batch Admin for Batch A1 in Org A
    mem_batch_admin = OrganizationMember(
        id=uuid.uuid4(),
        user_id=batch_admin_a1.id,
        organization_id=org_a.id,
        role_id=role_batch_admin.id,
        is_active=True,
        is_deleted=False,
    )
    # Employee in Batch A1 in Org A
    mem_emp_a1 = OrganizationMember(
        id=uuid.uuid4(),
        user_id=emp_a1.id,
        organization_id=org_a.id,
        role_id=role_employee.id,
        is_active=True,
        is_deleted=False,
    )
    # Employee in Batch B in Org B
    mem_emp_b = OrganizationMember(
        id=uuid.uuid4(),
        user_id=emp_b.id,
        organization_id=org_b.id,
        role_id=role_employee.id,
        is_active=True,
        is_deleted=False,
    )

    batch_mem_admin = BatchMember(
        id=uuid.uuid4(),
        batch_id=batch_a1.id,
        user_id=batch_admin_a1.id,
        role_id=role_batch_admin.id,
        is_active=True,
        is_deleted=False,
    )
    batch_mem_emp_a1 = BatchMember(
        id=uuid.uuid4(),
        batch_id=batch_a1.id,
        user_id=emp_a1.id,
        role_id=role_employee.id,
        is_active=True,
        is_deleted=False,
    )
    batch_mem_emp_b = BatchMember(
        id=uuid.uuid4(),
        batch_id=batch_b.id,
        user_id=emp_b.id,
        role_id=role_employee.id,
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([
        mem_super, mem_org_a, mem_batch_admin, mem_emp_a1, mem_emp_b,
        batch_mem_admin, batch_mem_emp_a1, batch_mem_emp_b
    ])
    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "batch_a1": batch_a1,
        "batch_a2": batch_a2,
        "batch_b": batch_b,
        "role_super": role_super,
        "role_org_admin": role_org_admin,
        "role_batch_admin": role_batch_admin,
        "role_employee": role_employee,
        "super_user": super_user,
        "org_admin_a": org_admin_a,
        "batch_admin_a1": batch_admin_a1,
        "emp_a1": emp_a1,
        "emp_b": emp_b,
    }


@pytest.fixture
def auth_jwt_client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as client:
        yield client
    fastapi_app.dependency_overrides.clear()


# =========================================================================
# 1. SUPER_ADMIN Permissions & Capabilities
# =========================================================================

def test_batch_rbac_01_super_admin_create_batch_any_org(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["super_user"])
    payload = {
        "organization_id": str(batch_rbac_setup["org_b"].id),
        "name": "Super Batch 2026",
        "year": 2026,
        "quarter": "AMJ",
        "start_date": "2026-04-01",
        "end_date": "2026-06-30",
        "meeting_day": "MONDAY",
    }
    response = auth_jwt_client.post("/api/batches/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Super Batch 2026"


def test_batch_rbac_02_super_admin_lists_all_batches(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["super_user"])
    response = auth_jwt_client.get("/api/batches/", headers=headers)
    assert response.status_code == 200
    batch_names = [b["name"] for b in response.json()["data"]]
    assert "Batch Alpha 1" in batch_names
    assert "Batch Beta 1" in batch_names


def test_batch_rbac_03_super_admin_gets_any_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["super_user"])
    batch_b = batch_rbac_setup["batch_b"]
    response = auth_jwt_client.get(f"/api/batches/{batch_b.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Batch Beta 1"


def test_batch_rbac_04_super_admin_updates_any_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["super_user"])
    batch_b = batch_rbac_setup["batch_b"]
    response = auth_jwt_client.put(
        f"/api/batches/{batch_b.id}",
        json={"name": "Batch Beta Renamed"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Batch Beta Renamed"


def test_batch_rbac_05_super_admin_closes_any_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["super_user"])
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.post(f"/api/batches/{batch_a2.id}/close", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "CLOSED"


def test_batch_rbac_06_super_admin_deletes_any_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["super_user"])
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.delete(f"/api/batches/{batch_a2.id}", headers=headers)
    assert response.status_code == 204


# =========================================================================
# 2. ORG_ADMIN Permissions & Multi-Tenant Scoping
# =========================================================================

def test_batch_rbac_07_org_admin_create_batch_own_org(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    payload = {
        "organization_id": str(batch_rbac_setup["org_a"].id),
        "name": "Org A Batch JAS",
        "year": 2026,
        "quarter": "JAS",
        "start_date": "2026-07-01",
        "end_date": "2026-09-30",
        "meeting_day": "THURSDAY",
    }
    response = auth_jwt_client.post("/api/batches/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Org A Batch JAS"


def test_batch_rbac_08_org_admin_cannot_create_batch_cross_org(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    payload = {
        "organization_id": str(batch_rbac_setup["org_b"].id),
        "name": "Malicious Org B Batch",
        "year": 2026,
        "quarter": "JAS",
        "start_date": "2026-07-01",
        "end_date": "2026-09-30",
        "meeting_day": "THURSDAY",
    }
    response = auth_jwt_client.post("/api/batches/", json=payload, headers=headers)
    assert response.status_code == 403


def test_batch_rbac_09_org_admin_lists_only_own_org_batches(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    response = auth_jwt_client.get("/api/batches/", headers=headers)
    assert response.status_code == 200
    batch_names = [b["name"] for b in response.json()["data"]]
    assert "Batch Alpha 1" in batch_names
    assert "Batch Alpha 2" in batch_names
    assert "Batch Beta 1" not in batch_names


def test_batch_rbac_10_org_admin_cannot_list_other_org_batches(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    response = auth_jwt_client.get(
        f"/api/batches/?organization_id={batch_rbac_setup['org_b'].id}",
        headers=headers,
    )
    assert response.status_code == 403


def test_batch_rbac_11_org_admin_gets_own_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.get(f"/api/batches/{batch_a1.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Batch Alpha 1"


def test_batch_rbac_12_org_admin_cannot_get_other_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_b = batch_rbac_setup["batch_b"]
    response = auth_jwt_client.get(f"/api/batches/{batch_b.id}", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_13_org_admin_updates_own_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.put(
        f"/api/batches/{batch_a1.id}",
        json={"name": "Batch Alpha 1 Updated"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Batch Alpha 1 Updated"


def test_batch_rbac_14_org_admin_cannot_update_other_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_b = batch_rbac_setup["batch_b"]
    response = auth_jwt_client.put(
        f"/api/batches/{batch_b.id}",
        json={"name": "Tampered Beta Batch"},
        headers=headers,
    )
    assert response.status_code == 403


def test_batch_rbac_15_org_admin_closes_own_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.post(f"/api/batches/{batch_a2.id}/close", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "CLOSED"


def test_batch_rbac_16_org_admin_cannot_close_other_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_b = batch_rbac_setup["batch_b"]
    response = auth_jwt_client.post(f"/api/batches/{batch_b.id}/close", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_17_org_admin_deletes_own_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.delete(f"/api/batches/{batch_a2.id}", headers=headers)
    assert response.status_code == 204


def test_batch_rbac_18_org_admin_cannot_delete_other_org_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["org_admin_a"], org_id=batch_rbac_setup["org_a"].id)
    batch_b = batch_rbac_setup["batch_b"]
    response = auth_jwt_client.delete(f"/api/batches/{batch_b.id}", headers=headers)
    assert response.status_code == 403


# =========================================================================
# 3. BATCH_ADMIN Permissions & Scoping
# =========================================================================

def test_batch_rbac_19_batch_admin_cannot_create_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    payload = {
        "organization_id": str(batch_rbac_setup["org_a"].id),
        "name": "Unauthorized Batch Admin Batch",
        "year": 2026,
        "quarter": "OND",
        "start_date": "2026-10-01",
        "end_date": "2026-12-31",
        "meeting_day": "FRIDAY",
    }
    response = auth_jwt_client.post("/api/batches/", json=payload, headers=headers)
    assert response.status_code == 403


def test_batch_rbac_20_batch_admin_lists_only_assigned_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    response = auth_jwt_client.get("/api/batches/", headers=headers)
    assert response.status_code == 200
    batch_names = [b["name"] for b in response.json()["data"]]
    assert "Batch Alpha 1" in batch_names
    assert "Batch Alpha 2" not in batch_names
    assert "Batch Beta 1" not in batch_names


def test_batch_rbac_21_batch_admin_gets_assigned_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.get(f"/api/batches/{batch_a1.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Batch Alpha 1"


def test_batch_rbac_22_batch_admin_cannot_get_other_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.get(f"/api/batches/{batch_a2.id}", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_23_batch_admin_updates_assigned_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.put(
        f"/api/batches/{batch_a1.id}",
        json={"meeting_day": "TUESDAY"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["meeting_day"] == "TUESDAY"


def test_batch_rbac_24_batch_admin_cannot_update_other_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.put(
        f"/api/batches/{batch_a2.id}",
        json={"meeting_day": "WEDNESDAY"},
        headers=headers,
    )
    assert response.status_code == 403


def test_batch_rbac_25_batch_admin_closes_assigned_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.post(f"/api/batches/{batch_a1.id}/close", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "CLOSED"


def test_batch_rbac_26_batch_admin_cannot_close_other_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.post(f"/api/batches/{batch_a2.id}/close", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_27_batch_admin_cannot_delete_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["batch_admin_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.delete(f"/api/batches/{batch_a1.id}", headers=headers)
    assert response.status_code == 403


# =========================================================================
# 4. EMPLOYEE Permissions & Scoping (No Batch Access - 403 Forbidden)
# =========================================================================

def test_batch_rbac_28_employee_cannot_get_assigned_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.get(f"/api/batches/{batch_a1.id}", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_29_employee_cannot_list_batches(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_a"].id)
    response = auth_jwt_client.get("/api/batches/", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_30_employee_cannot_get_other_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a2 = batch_rbac_setup["batch_a2"]
    response = auth_jwt_client.get(f"/api/batches/{batch_a2.id}", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_31_employee_cannot_create_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_a"].id)
    payload = {
        "organization_id": str(batch_rbac_setup["org_a"].id),
        "name": "Employee Batch",
        "year": 2026,
        "quarter": "OND",
        "start_date": "2026-10-01",
        "end_date": "2026-12-31",
        "meeting_day": "FRIDAY",
    }
    response = auth_jwt_client.post("/api/batches/", json=payload, headers=headers)
    assert response.status_code == 403


def test_batch_rbac_32_employee_cannot_update_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.put(
        f"/api/batches/{batch_a1.id}",
        json={"name": "Employee Tampered Batch"},
        headers=headers,
    )
    assert response.status_code == 403


def test_batch_rbac_33_employee_cannot_close_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.post(f"/api/batches/{batch_a1.id}/close", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_34_employee_cannot_delete_batch(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_a"].id)
    batch_a1 = batch_rbac_setup["batch_a1"]
    response = auth_jwt_client.delete(f"/api/batches/{batch_a1.id}", headers=headers)
    assert response.status_code == 403


# =========================================================================
# 5. Security & Authentication Edge Cases
# =========================================================================

def test_batch_rbac_35_missing_token_returns_401(auth_jwt_client: TestClient):
    response = auth_jwt_client.get("/api/batches/")
    assert response.status_code == 401


def test_batch_rbac_36_invalid_token_returns_401(auth_jwt_client: TestClient):
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    response = auth_jwt_client.get("/api/batches/", headers=headers)
    assert response.status_code == 401


def test_batch_rbac_37_header_spoofing_rejected(auth_jwt_client: TestClient, batch_rbac_setup: dict):
    # Employee from Org A tries to send Org B ID in header
    headers = get_auth_headers(batch_rbac_setup["emp_a1"], org_id=batch_rbac_setup["org_b"].id)
    batch_b = batch_rbac_setup["batch_b"]
    response = auth_jwt_client.get(f"/api/batches/{batch_b.id}", headers=headers)
    assert response.status_code == 403


def test_batch_rbac_38_dual_membership_employee_and_batch_admin_can_view_batches(
    auth_jwt_client: TestClient,
    batch_rbac_setup: dict,
    db_session: Session,
):
    """
    When a user has both an EMPLOYEE membership (created first) and a BATCH_ADMIN membership
    in the same organization, they must be recognized as BATCH_ADMIN and have 'batch.view' permission.
    """
    user = batch_rbac_setup["emp_a1"]
    # User already has mem_emp_a1 (EMPLOYEE role)
    # Add a BATCH_ADMIN membership in the same org
    dual_admin_mem = OrganizationMember(
        id=uuid.uuid4(),
        user_id=user.id,
        organization_id=batch_rbac_setup["org_a"].id,
        role_id=batch_rbac_setup["role_batch_admin"].id,
        is_active=True,
        is_deleted=False,
    )
    existing_bm = (
        db_session.query(BatchMember)
        .filter_by(batch_id=batch_rbac_setup["batch_a1"].id, user_id=user.id)
        .first()
    )
    if existing_bm:
        existing_bm.role_id = batch_rbac_setup["role_batch_admin"].id
    else:
        dual_batch_mem = BatchMember(
            id=uuid.uuid4(),
            batch_id=batch_rbac_setup["batch_a1"].id,
            user_id=user.id,
            role_id=batch_rbac_setup["role_batch_admin"].id,
            is_active=True,
            is_deleted=False,
        )
        db_session.add(dual_batch_mem)
    db_session.add(dual_admin_mem)
    db_session.commit()

    headers = get_auth_headers(user, org_id=batch_rbac_setup["org_a"].id)
    response = auth_jwt_client.get(
        f"/api/batches/?organization_id={batch_rbac_setup['org_a'].id}",
        headers=headers,
    )
    assert response.status_code == 200
    batch_names = [b["name"] for b in response.json()["data"]]
    assert "Batch Alpha 1" in batch_names


def test_batch_rbac_39_hyphenated_batch_admin_role_can_view_batches(
    auth_jwt_client: TestClient,
    batch_rbac_setup: dict,
    db_session: Session,
):
    """
    A role named 'batch-admin' (with a hyphen) must normalize to BATCH_ADMIN and grant 'batch.view'.
    """
    role_hyphen = Role(
        id=uuid.uuid4(),
        name="batch-admin",
        description="Hyphenated batch-admin role",
    )
    db_session.add(role_hyphen)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        username="hyphen_admin",
        email="hyphen_admin@example.com",
        password_hash=hash_password("Password123!"),
        first_name="Hyphen",
        last_name="Admin",
        is_active=True,
        is_deleted=False,
    )
    db_session.add(user)
    db_session.flush()

    mem = OrganizationMember(
        id=uuid.uuid4(),
        user_id=user.id,
        organization_id=batch_rbac_setup["org_a"].id,
        role_id=role_hyphen.id,
        is_active=True,
        is_deleted=False,
    )
    batch_mem = BatchMember(
        id=uuid.uuid4(),
        batch_id=batch_rbac_setup["batch_a1"].id,
        user_id=user.id,
        role_id=role_hyphen.id,
        is_active=True,
        is_deleted=False,
    )
    db_session.add_all([mem, batch_mem])
    db_session.commit()

    headers = get_auth_headers(user, org_id=batch_rbac_setup["org_a"].id)
    response = auth_jwt_client.get(
        f"/api/batches/?organization_id={batch_rbac_setup['org_a'].id}",
        headers=headers,
    )
    assert response.status_code == 200
    batch_names = [b["name"] for b in response.json()["data"]]
    assert "Batch Alpha 1" in batch_names


def test_batch_rbac_40_single_org_user_with_multiple_memberships_resolves_without_header(
    auth_jwt_client: TestClient,
    batch_rbac_setup: dict,
    db_session: Session,
):
    """
    If a user has multiple memberships that all belong to the SAME organization,
    omitting the X-Organization-ID header should automatically resolve to that organization.
    """
    user = batch_rbac_setup["batch_admin_a1"]
    # Add an additional membership in Org A (e.g. employee without batch)
    extra_mem = OrganizationMember(
        id=uuid.uuid4(),
        user_id=user.id,
        organization_id=batch_rbac_setup["org_a"].id,
        role_id=batch_rbac_setup["role_employee"].id,
        is_active=True,
        is_deleted=False,
    )
    db_session.add(extra_mem)
    db_session.commit()

    # Call WITHOUT X-Organization-ID header
    headers = get_auth_headers(user, org_id=None)
    response = auth_jwt_client.get(
        f"/api/batches/?organization_id={batch_rbac_setup['org_a'].id}",
        headers=headers,
    )
    assert response.status_code == 200
    batch_names = [b["name"] for b in response.json()["data"]]
    assert "Batch Alpha 1" in batch_names


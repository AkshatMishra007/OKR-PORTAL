"""
Role-Based Access Control (RBAC) & Multi-Tenancy Tests for FOGS & Hurdles Module.

Validates permissions, tenant boundaries, batch scoping, and lifecycle rules:
- SUPER_ADMIN: Global CRUD & management across all organizations.
- ORG_ADMIN: Scoped CRUD & management within own organization. Cross-org denied (403).
- BATCH_ADMIN: Scoped view, create, update, and delete in assigned batch. Other batches/orgs denied (403).
- EMPLOYEE: Scoped CRUD on own assigned OKRs. Read-only on batch peer OKRs. Peer/cross-org mutations denied (403).
- Closed Batch Protection: All mutations (create, update, delete) on closed batch OKRs denied (400).
- Security: Missing/invalid JWT (401).
"""

import uuid
from datetime import date
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.batches.models import Batch, BatchStatus, MeetingDay, Quarter
from app.core.database import get_db
from app.fogs_hurdles.models import FogsHurdle
from app.main import app as fastapi_app
from app.my_okr.models import OKR
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


def get_auth_headers(user: User, org_id: uuid.UUID | None = None) -> dict:
    """Generate JWT authorization headers and optional X-Organization-ID header."""
    token = create_access_token({"sub": str(user.id), "email": user.email, "username": user.username})
    headers = {"Authorization": f"Bearer {token}"}
    if org_id:
        headers["X-Organization-ID"] = str(org_id)
    return headers


@pytest.fixture
def auth_jwt_client(db_session: Session):
    """TestClient that uses real token decoding against test database."""
    def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    if get_current_user in fastapi_app.dependency_overrides:
        del fastapi_app.dependency_overrides[get_current_user]

    with TestClient(fastapi_app) as c:
        yield c

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def fogs_hurdle_rbac_setup(db_session: Session):
    """
    Sets up a comprehensive multi-organization, multi-batch, multi-role test fixture:
    - 2 Organizations (org_a, org_b)
    - 3 Batches (batch_a1 active, batch_a_closed closed in org_a; batch_b active in org_b)
    - 4 Roles (SUPER_ADMIN, ORG_ADMIN, BATCH_ADMIN, EMPLOYEE)
    - Users assigned to roles
    - OKRs and initial FOGS & Hurdles
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
    batch_a_closed = Batch(
        id=uuid.uuid4(),
        name="Batch Alpha Closed",
        year=2025,
        quarter=Quarter.OND,
        start_date=date(2025, 10, 1),
        end_date=date(2025, 12, 31),
        meeting_day=MeetingDay.FRIDAY,
        status=BatchStatus.CLOSED,
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
    db_session.add_all([batch_a1, batch_a_closed, batch_b])
    db_session.flush()

    # 3. Roles
    def get_or_create_role(name: str) -> Role:
        role = db_session.query(Role).filter(Role.name == name).first()
        if not role:
            role = Role(id=uuid.uuid4(), name=name, description=f"{name} role")
            db_session.add(role)
            db_session.flush()
        return role

    role_super = get_or_create_role("SUPER_ADMIN")
    role_org_admin = get_or_create_role("ORG_ADMIN")
    role_batch_admin = get_or_create_role("BATCH_ADMIN")
    role_employee = get_or_create_role("EMPLOYEE")

    # 4. Users
    pwd = hash_password("Password123!")

    super_user = User(
        id=uuid.uuid4(),
        username="superadmin_fh",
        email="superadmin_fh@example.com",
        password_hash=pwd,
        first_name="Super",
        last_name="Admin",
        is_active=True,
        is_deleted=False,
    )
    org_admin_a = User(
        id=uuid.uuid4(),
        username="orgadmin_a_fh",
        email="orgadmin_a_fh@example.com",
        password_hash=pwd,
        first_name="OrgAdmin",
        last_name="A",
        is_active=True,
        is_deleted=False,
    )
    batch_admin_a1 = User(
        id=uuid.uuid4(),
        username="batchadmin_a1_fh",
        email="batchadmin_a1_fh@example.com",
        password_hash=pwd,
        first_name="BatchAdmin",
        last_name="A1",
        is_active=True,
        is_deleted=False,
    )
    emp_a1 = User(
        id=uuid.uuid4(),
        username="employee_a1_fh",
        email="emp_a1_fh@example.com",
        password_hash=pwd,
        first_name="Employee",
        last_name="A1",
        is_active=True,
        is_deleted=False,
    )
    emp_a2 = User(
        id=uuid.uuid4(),
        username="employee_a2_fh",
        email="emp_a2_fh@example.com",
        password_hash=pwd,
        first_name="Employee",
        last_name="A2",
        is_active=True,
        is_deleted=False,
    )
    emp_closed = User(
        id=uuid.uuid4(),
        username="employee_closed_fh",
        email="emp_closed_fh@example.com",
        password_hash=pwd,
        first_name="Employee",
        last_name="Closed",
        is_active=True,
        is_deleted=False,
    )
    emp_b = User(
        id=uuid.uuid4(),
        username="employee_b_fh",
        email="emp_b_fh@example.com",
        password_hash=pwd,
        first_name="Employee",
        last_name="B",
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([super_user, org_admin_a, batch_admin_a1, emp_a1, emp_a2, emp_closed, emp_b])
    db_session.flush()

    # 5. Organization Memberships
    mem_super = OrganizationMember(
        id=uuid.uuid4(),
        user_id=super_user.id,
        organization_id=org_a.id,
        role_id=role_super.id,
        is_active=True,
        is_deleted=False,
    )
    mem_org_a = OrganizationMember(
        id=uuid.uuid4(),
        user_id=org_admin_a.id,
        organization_id=org_a.id,
        role_id=role_org_admin.id,
        is_active=True,
        is_deleted=False,
    )
    mem_batch_admin = OrganizationMember(
        id=uuid.uuid4(),
        user_id=batch_admin_a1.id,
        organization_id=org_a.id,
        role_id=role_batch_admin.id,
        batch_id=batch_a1.id,
        is_active=True,
        is_deleted=False,
    )
    mem_emp_a1 = OrganizationMember(
        id=uuid.uuid4(),
        user_id=emp_a1.id,
        organization_id=org_a.id,
        role_id=role_employee.id,
        batch_id=batch_a1.id,
        is_active=True,
        is_deleted=False,
    )
    mem_emp_a2 = OrganizationMember(
        id=uuid.uuid4(),
        user_id=emp_a2.id,
        organization_id=org_a.id,
        role_id=role_employee.id,
        batch_id=batch_a1.id,
        is_active=True,
        is_deleted=False,
    )
    mem_emp_closed = OrganizationMember(
        id=uuid.uuid4(),
        user_id=emp_closed.id,
        organization_id=org_a.id,
        role_id=role_employee.id,
        batch_id=batch_a_closed.id,
        is_active=True,
        is_deleted=False,
    )
    mem_emp_b = OrganizationMember(
        id=uuid.uuid4(),
        user_id=emp_b.id,
        organization_id=org_b.id,
        role_id=role_employee.id,
        batch_id=batch_b.id,
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([mem_super, mem_org_a, mem_batch_admin, mem_emp_a1, mem_emp_a2, mem_emp_closed, mem_emp_b])
    db_session.flush()

    # 6. OKRs
    okr_emp_a1 = OKR(
        id=uuid.uuid4(),
        batch_id=batch_a1.id,
        assigned_to=mem_emp_a1.id,
        objective="Deliver Q1 Backend Architecture",
        okr_type="PROFESSIONAL",
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )
    okr_emp_a2 = OKR(
        id=uuid.uuid4(),
        batch_id=batch_a1.id,
        assigned_to=mem_emp_a2.id,
        objective="Implement Frontend Design System",
        okr_type="PROFESSIONAL",
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )
    okr_closed = OKR(
        id=uuid.uuid4(),
        batch_id=batch_a_closed.id,
        assigned_to=mem_emp_closed.id,
        objective="Historical Q4 Deliverable",
        okr_type="PROFESSIONAL",
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )
    okr_emp_b = OKR(
        id=uuid.uuid4(),
        batch_id=batch_b.id,
        assigned_to=mem_emp_b.id,
        objective="Org B Sales Target",
        okr_type="PROFESSIONAL",
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([okr_emp_a1, okr_emp_a2, okr_closed, okr_emp_b])
    db_session.flush()

    # 7. Initial FOGS & Hurdles
    hurdle_emp_a1 = FogsHurdle(
        id=uuid.uuid4(),
        okr_id=okr_emp_a1.id,
        fogs_hurdles="Database query latency high",
        action_points="Add indexing and optimize joins",
        created_by=emp_a1.id,
        is_active=True,
        is_deleted=False,
    )
    hurdle_emp_a2 = FogsHurdle(
        id=uuid.uuid4(),
        okr_id=okr_emp_a2.id,
        fogs_hurdles="UI mockups not approved",
        action_points="Review with product designer",
        created_by=emp_a2.id,
        is_active=True,
        is_deleted=False,
    )
    hurdle_closed = FogsHurdle(
        id=uuid.uuid4(),
        okr_id=okr_closed.id,
        fogs_hurdles="Legacy API deprecated",
        action_points="Migrated to v2 endpoint",
        created_by=emp_closed.id,
        is_active=True,
        is_deleted=False,
    )
    hurdle_emp_b = FogsHurdle(
        id=uuid.uuid4(),
        okr_id=okr_emp_b.id,
        fogs_hurdles="Contract negotiations slow",
        action_points="Involve legal counsel",
        created_by=emp_b.id,
        is_active=True,
        is_deleted=False,
    )

    db_session.add_all([hurdle_emp_a1, hurdle_emp_a2, hurdle_closed, hurdle_emp_b])
    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "batch_a1": batch_a1,
        "batch_a_closed": batch_a_closed,
        "batch_b": batch_b,
        "super_user": super_user,
        "org_admin_a": org_admin_a,
        "batch_admin_a1": batch_admin_a1,
        "emp_a1": emp_a1,
        "emp_a2": emp_a2,
        "emp_closed": emp_closed,
        "emp_b": emp_b,
        "okr_emp_a1": okr_emp_a1,
        "okr_emp_a2": okr_emp_a2,
        "okr_closed": okr_closed,
        "okr_emp_b": okr_emp_b,
        "hurdle_emp_a1": hurdle_emp_a1,
        "hurdle_emp_a2": hurdle_emp_a2,
        "hurdle_closed": hurdle_closed,
        "hurdle_emp_b": hurdle_emp_b,
    }


# ==============================================================================
# 1. SUPER_ADMIN SCENARIOS
# ==============================================================================

def test_fogs_hurdle_rbac_01_super_admin_create_hurdle_any_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Super Admin can create a FOGS & Hurdle on any OKR across any organization."""
    super_user = fogs_hurdle_rbac_setup["super_user"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(super_user)

    payload = {
        "fogs_hurdles": "Super Admin identified resource bottleneck",
        "action_points": "Allocate cloud infrastructure credits",
    }
    response = auth_jwt_client.post(f"/okrs/{okr_b.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["fogs_hurdles"] == payload["fogs_hurdles"]
    assert data["okr_id"] == str(okr_b.id)


def test_fogs_hurdle_rbac_02_super_admin_lists_hurdles_for_any_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Super Admin can list hurdles for any OKR across organizations."""
    super_user = fogs_hurdle_rbac_setup["super_user"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(super_user)

    response = auth_jwt_client.get(f"/okrs/{okr_b.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) >= 1


def test_fogs_hurdle_rbac_03_super_admin_gets_any_hurdle(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Super Admin can retrieve any individual FOGS & Hurdle by ID."""
    super_user = fogs_hurdle_rbac_setup["super_user"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(super_user)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(hurdle_b.id)


def test_fogs_hurdle_rbac_04_super_admin_updates_any_hurdle(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Super Admin can update any FOGS & Hurdle entry."""
    super_user = fogs_hurdle_rbac_setup["super_user"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(super_user)

    payload = {"fogs_hurdles": "Updated by Super Admin globally"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_b.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["fogs_hurdles"] == "Updated by Super Admin globally"


def test_fogs_hurdle_rbac_05_super_admin_deletes_any_hurdle(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Super Admin can soft-delete any FOGS & Hurdle entry."""
    super_user = fogs_hurdle_rbac_setup["super_user"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(super_user)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


# ==============================================================================
# 2. ORG_ADMIN SCENARIOS
# ==============================================================================

def test_fogs_hurdle_rbac_06_org_admin_create_hurdle_own_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin can create a hurdle for any OKR within their own organization."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    headers = get_auth_headers(org_admin)

    payload = {
        "fogs_hurdles": "Org Admin blocker note",
        "action_points": "Action point from leadership",
    }
    response = auth_jwt_client.post(f"/okrs/{okr_a1.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["fogs_hurdles"] == payload["fogs_hurdles"]


def test_fogs_hurdle_rbac_07_org_admin_cannot_create_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin cannot create a hurdle for an OKR in another organization (403)."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(org_admin)

    payload = {"fogs_hurdles": "Cross-org attempt"}
    response = auth_jwt_client.post(f"/okrs/{okr_b.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_08_org_admin_lists_hurdles_own_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin can list hurdles for OKRs within their own organization."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    headers = get_auth_headers(org_admin)

    response = auth_jwt_client.get(f"/okrs/{okr_a1.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_09_org_admin_cannot_list_hurdles_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin cannot list hurdles for an OKR in another organization (403)."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(org_admin)

    response = auth_jwt_client.get(f"/okrs/{okr_b.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_10_org_admin_gets_hurdle_own_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin can get a hurdle record within their own organization."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(org_admin)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_a1.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_11_org_admin_cannot_get_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin cannot retrieve a hurdle record belonging to another organization (403)."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(org_admin)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_12_org_admin_updates_hurdle_own_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin can update any hurdle record within their organization."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(org_admin)

    payload = {"fogs_hurdles": "Updated by Org Admin"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_a1.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["fogs_hurdles"] == "Updated by Org Admin"


def test_fogs_hurdle_rbac_13_org_admin_cannot_update_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin cannot update a hurdle belonging to another organization (403)."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(org_admin)

    payload = {"fogs_hurdles": "Unauthorized Org Admin update"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_b.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_14_org_admin_deletes_hurdle_own_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin can delete a hurdle record within their own organization."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(org_admin)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_a1.id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_fogs_hurdle_rbac_15_org_admin_cannot_delete_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Org Admin cannot delete a hurdle record in another organization (403)."""
    org_admin = fogs_hurdle_rbac_setup["org_admin_a"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(org_admin)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# 3. BATCH_ADMIN SCENARIOS
# ==============================================================================

def test_fogs_hurdle_rbac_16_batch_admin_create_hurdle_assigned_batch(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin can create a hurdle for an OKR in their assigned batch cohort."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    headers = get_auth_headers(batch_admin)

    payload = {
        "fogs_hurdles": "Batch Admin flagged blocker",
        "action_points": "Follow up in next sprint meeting",
    }
    response = auth_jwt_client.post(f"/okrs/{okr_a1.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED


def test_fogs_hurdle_rbac_17_batch_admin_cannot_create_hurdle_other_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin cannot create a hurdle for an OKR in another organization (403)."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(batch_admin)

    payload = {"fogs_hurdles": "Cross org hurdle attempt"}
    response = auth_jwt_client.post(f"/okrs/{okr_b.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_18_batch_admin_lists_hurdles_assigned_batch(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin can list hurdles for OKRs within their assigned batch."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    headers = get_auth_headers(batch_admin)

    response = auth_jwt_client.get(f"/okrs/{okr_a1.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_19_batch_admin_cannot_list_hurdles_other_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin cannot list hurdles for OKRs in another organization (403)."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(batch_admin)

    response = auth_jwt_client.get(f"/okrs/{okr_b.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_20_batch_admin_gets_hurdle_assigned_batch(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin can get an individual hurdle record within their assigned batch."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(batch_admin)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_a1.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_21_batch_admin_cannot_get_hurdle_other_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin cannot get a hurdle record belonging to another organization (403)."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(batch_admin)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_22_batch_admin_updates_hurdle_assigned_batch(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin can update a hurdle record in their assigned batch."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(batch_admin)

    payload = {"fogs_hurdles": "Batch Admin refined blocker details"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_a1.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_23_batch_admin_cannot_update_hurdle_other_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin cannot update a hurdle in another organization (403)."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(batch_admin)

    payload = {"fogs_hurdles": "Cross org update attempt"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_b.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_24_batch_admin_deletes_hurdle_assigned_batch(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin can delete a hurdle record in their assigned batch."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(batch_admin)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_a1.id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_fogs_hurdle_rbac_25_batch_admin_cannot_delete_hurdle_other_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Batch Admin cannot delete a hurdle in another organization (403)."""
    batch_admin = fogs_hurdle_rbac_setup["batch_admin_a1"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(batch_admin)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# 4. EMPLOYEE SCENARIOS
# ==============================================================================

def test_fogs_hurdle_rbac_26_employee_create_hurdle_own_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee can create a FOGS & Hurdle on their own assigned OKR."""
    emp = fogs_hurdle_rbac_setup["emp_a1"]
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    headers = get_auth_headers(emp)

    payload = {
        "fogs_hurdles": "Lack of testing environments",
        "action_points": "Request sandbox cluster from DevOps",
    }
    response = auth_jwt_client.post(f"/okrs/{okr_a1.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["fogs_hurdles"] == payload["fogs_hurdles"]


def test_fogs_hurdle_rbac_27_employee_cannot_create_hurdle_peer_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot create a hurdle on another employee's OKR (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    okr_a2 = fogs_hurdle_rbac_setup["okr_emp_a2"]  # Assigned to emp_a2
    headers = get_auth_headers(emp_a1)

    payload = {"fogs_hurdles": "Attempting to add hurdle to peer OKR"}
    response = auth_jwt_client.post(f"/okrs/{okr_a2.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_28_employee_cannot_create_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot create a hurdle on an OKR in another organization (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(emp_a1)

    payload = {"fogs_hurdles": "Cross org hurdle"}
    response = auth_jwt_client.post(f"/okrs/{okr_b.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_29_employee_lists_hurdles_own_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee can list hurdles for their own OKR."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.get(f"/okrs/{okr_a1.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_30_employee_lists_hurdles_peer_okr_in_batch(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee can view hurdles on a peer's OKR within their assigned batch cohort."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    okr_a2 = fogs_hurdle_rbac_setup["okr_emp_a2"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.get(f"/okrs/{okr_a2.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_31_employee_cannot_list_hurdles_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot view hurdles on an OKR in another organization (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    okr_b = fogs_hurdle_rbac_setup["okr_emp_b"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.get(f"/okrs/{okr_b.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_32_employee_gets_hurdle_own_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee can get an individual hurdle record on their own OKR."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_a1.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_33_employee_gets_hurdle_peer_okr_in_batch(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee can view an individual hurdle record on a peer's OKR within their batch."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_a2 = fogs_hurdle_rbac_setup["hurdle_emp_a2"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_a2.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_fogs_hurdle_rbac_34_employee_cannot_get_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot view a hurdle belonging to an OKR in another organization (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.get(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_35_employee_updates_hurdle_own_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee can update a hurdle on their own assigned OKR."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(emp_a1)

    payload = {"fogs_hurdles": "Updated by employee on own OKR"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_a1.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["fogs_hurdles"] == "Updated by employee on own OKR"


def test_fogs_hurdle_rbac_36_employee_cannot_update_hurdle_peer_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot update a hurdle on another employee's OKR (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_a2 = fogs_hurdle_rbac_setup["hurdle_emp_a2"]
    headers = get_auth_headers(emp_a1)

    payload = {"fogs_hurdles": "Attempting to edit peer hurdle"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_a2.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_37_employee_cannot_update_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot update a hurdle in another organization (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(emp_a1)

    payload = {"fogs_hurdles": "Cross org update"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_b.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_38_employee_deletes_hurdle_own_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee can delete a hurdle on their own assigned OKR."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_a1.id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_fogs_hurdle_rbac_39_employee_cannot_delete_hurdle_peer_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot delete a hurdle on another employee's OKR (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_a2 = fogs_hurdle_rbac_setup["hurdle_emp_a2"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_a2.id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_fogs_hurdle_rbac_40_employee_cannot_delete_hurdle_cross_org(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Employee cannot delete a hurdle in another organization (403)."""
    emp_a1 = fogs_hurdle_rbac_setup["emp_a1"]
    hurdle_b = fogs_hurdle_rbac_setup["hurdle_emp_b"]
    headers = get_auth_headers(emp_a1)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_b.id}", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# 5. CLOSED BATCH IMMUTABILITY SCENARIOS
# ==============================================================================

def test_fogs_hurdle_rbac_41_cannot_create_hurdle_on_closed_batch_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Creating a hurdle on an OKR belonging to a closed batch is rejected with 400 Bad Request."""
    emp_closed = fogs_hurdle_rbac_setup["emp_closed"]
    okr_closed = fogs_hurdle_rbac_setup["okr_closed"]
    headers = get_auth_headers(emp_closed)

    payload = {"fogs_hurdles": "Hurdle in closed batch"}
    response = auth_jwt_client.post(f"/okrs/{okr_closed.id}/fogs-hurdles", json=payload, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "closed and read-only" in response.json()["detail"]


def test_fogs_hurdle_rbac_42_cannot_update_hurdle_on_closed_batch_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Updating a hurdle on an OKR belonging to a closed batch is rejected with 400 Bad Request."""
    emp_closed = fogs_hurdle_rbac_setup["emp_closed"]
    hurdle_closed = fogs_hurdle_rbac_setup["hurdle_closed"]
    headers = get_auth_headers(emp_closed)

    payload = {"fogs_hurdles": "Attempting update on closed batch"}
    response = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_closed.id}", json=payload, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "closed and read-only" in response.json()["detail"]


def test_fogs_hurdle_rbac_43_cannot_delete_hurdle_on_closed_batch_okr(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Deleting a hurdle on an OKR belonging to a closed batch is rejected with 400 Bad Request."""
    emp_closed = fogs_hurdle_rbac_setup["emp_closed"]
    hurdle_closed = fogs_hurdle_rbac_setup["hurdle_closed"]
    headers = get_auth_headers(emp_closed)

    response = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_closed.id}", headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "closed and read-only" in response.json()["detail"]


# ==============================================================================
# 6. AUTHENTICATION & TOKEN SECURITY SCENARIOS
# ==============================================================================

def test_fogs_hurdle_rbac_44_missing_token_returns_401(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Unauthenticated requests without Authorization header return 401 Unauthorized."""
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    hurdle_a1 = fogs_hurdle_rbac_setup["hurdle_emp_a1"]

    # POST without token
    res_post = auth_jwt_client.post(f"/okrs/{okr_a1.id}/fogs-hurdles", json={"fogs_hurdles": "Anon"})
    assert res_post.status_code == status.HTTP_401_UNAUTHORIZED

    # GET without token
    res_get = auth_jwt_client.get(f"/okrs/{okr_a1.id}/fogs-hurdles")
    assert res_get.status_code == status.HTTP_401_UNAUTHORIZED

    # PUT without token
    res_put = auth_jwt_client.put(f"/fogs-hurdles/{hurdle_a1.id}", json={"fogs_hurdles": "Anon"})
    assert res_put.status_code == status.HTTP_401_UNAUTHORIZED

    # DELETE without token
    res_del = auth_jwt_client.delete(f"/fogs-hurdles/{hurdle_a1.id}")
    assert res_del.status_code == status.HTTP_401_UNAUTHORIZED


def test_fogs_hurdle_rbac_45_invalid_token_returns_401(auth_jwt_client: TestClient, fogs_hurdle_rbac_setup):
    """Requests with malformed or invalid JWT tokens return 401 Unauthorized."""
    okr_a1 = fogs_hurdle_rbac_setup["okr_emp_a1"]
    headers = {"Authorization": "Bearer invalid.jwt.token.here"}

    response = auth_jwt_client.get(f"/okrs/{okr_a1.id}/fogs-hurdles", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

from datetime import date
import uuid
import pytest
from fastapi import status

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.batches.models import Batch, BatchMember, MeetingDay, Quarter
from app.my_okr.models import OKR
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


from app.auth.dependencies import get_current_user
from app.main import app as fastapi_app


@pytest.fixture
def authz_setup(db_session):
    # Ensure real JWT authentication runs by removing the dummy get_current_user override from conftest
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    # Organizations
    org_a = Organization(name="Org A", is_active=True, is_deleted=False)
    org_b = Organization(name="Org B", is_active=True, is_deleted=False)
    db_session.add_all([org_a, org_b])
    db_session.commit()

    # Roles
    role_emp = Role(name="EMPLOYEE", is_active=True, is_deleted=False)
    role_batch_admin = Role(name="BATCH_ADMIN", is_active=True, is_deleted=False)
    role_org_admin = Role(name="ORG_ADMIN", is_active=True, is_deleted=False)
    db_session.add_all([role_emp, role_batch_admin, role_org_admin])
    db_session.commit()

    # Batches in Org A
    batch_a1 = Batch(
        name="Batch A1",
        quarter=Quarter.JFM,
        year=2026,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        organization_id=org_a.id,
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )
    batch_a2 = Batch(
        name="Batch A2",
        quarter=Quarter.AMJ,
        year=2026,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.TUESDAY,
        organization_id=org_a.id,
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )
    # Batch in Org B
    batch_b1 = Batch(
        name="Batch B1",
        quarter=Quarter.JFM,
        year=2026,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        organization_id=org_b.id,
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )
    db_session.add_all([batch_a1, batch_a2, batch_b1])
    db_session.commit()

    # Users
    user_emp_a = User(username="emp_a", email="emp_a@test.com", password_hash=hash_password("Pass123!"), first_name="EmpA", is_deleted=False)
    user_emp_b = User(username="emp_b", email="emp_b@test.com", password_hash=hash_password("Pass123!"), first_name="EmpB", is_deleted=False)
    user_batch_admin = User(username="b_admin", email="b_admin@test.com", password_hash=hash_password("Pass123!"), first_name="BatchAdmin", is_deleted=False)
    user_org_admin = User(username="org_admin", email="org_admin@test.com", password_hash=hash_password("Pass123!"), first_name="OrgAdmin", is_deleted=False)
    user_org_b = User(username="user_b", email="user_b@test.com", password_hash=hash_password("Pass123!"), first_name="UserB", is_deleted=False)

    db_session.add_all([user_emp_a, user_emp_b, user_batch_admin, user_org_admin, user_org_b])
    db_session.commit()

    # Organization Members
    mem_emp_a = OrganizationMember(user_id=user_emp_a.id, organization_id=org_a.id, role_id=role_emp.id, is_active=True, is_deleted=False)
    mem_emp_b = OrganizationMember(user_id=user_emp_b.id, organization_id=org_a.id, role_id=role_emp.id, is_active=True, is_deleted=False)
    mem_batch_admin = OrganizationMember(user_id=user_batch_admin.id, organization_id=org_a.id, role_id=role_batch_admin.id, is_active=True, is_deleted=False)
    mem_org_admin = OrganizationMember(user_id=user_org_admin.id, organization_id=org_a.id, role_id=role_org_admin.id, is_active=True, is_deleted=False)
    mem_org_b = OrganizationMember(user_id=user_org_b.id, organization_id=org_b.id, role_id=role_emp.id, is_active=True, is_deleted=False)

    # Batch Members
    bm_emp_a = BatchMember(batch_id=batch_a1.id, user_id=user_emp_a.id, role_id=role_emp.id, is_active=True, is_deleted=False)
    bm_emp_b = BatchMember(batch_id=batch_a1.id, user_id=user_emp_b.id, role_id=role_emp.id, is_active=True, is_deleted=False)
    bm_batch_admin = BatchMember(batch_id=batch_a1.id, user_id=user_batch_admin.id, role_id=role_batch_admin.id, is_active=True, is_deleted=False)
    bm_org_b = BatchMember(batch_id=batch_b1.id, user_id=user_org_b.id, role_id=role_emp.id, is_active=True, is_deleted=False)

    db_session.add_all([mem_emp_a, mem_emp_b, mem_batch_admin, mem_org_admin, mem_org_b, bm_emp_a, bm_emp_b, bm_batch_admin, bm_org_b])
    db_session.commit()

    # OKRs
    okr_b = OKR(batch_id=batch_a1.id, assigned_to=mem_emp_b.id, objective="Emp B OKR", okr_type="STANDARD", is_active=True, is_deleted=False)
    okr_a2 = OKR(batch_id=batch_a2.id, assigned_to=mem_emp_b.id, objective="Batch A2 OKR", okr_type="STANDARD", is_active=True, is_deleted=False)
    okr_org_b = OKR(batch_id=batch_b1.id, assigned_to=mem_org_b.id, objective="Org B OKR", okr_type="STANDARD", is_active=True, is_deleted=False)

    db_session.add_all([okr_b, okr_a2, okr_org_b])
    db_session.commit()

    def get_headers(user):
        token = create_access_token({"sub": str(user.id), "email": user.email, "username": user.username})
        return {"Authorization": f"Bearer {token}"}

    return {
        "org_a": org_a,
        "org_b": org_b,
        "batch_a1": batch_a1,
        "batch_a2": batch_a2,
        "batch_b1": batch_b1,
        "user_emp_a": user_emp_a,
        "user_emp_b": user_emp_b,
        "user_batch_admin": user_batch_admin,
        "user_org_admin": user_org_admin,
        "user_org_b": user_org_b,
        "okr_b": okr_b,
        "okr_a2": okr_a2,
        "okr_org_b": okr_org_b,
        "headers_emp_a": get_headers(user_emp_a),
        "headers_batch_admin": get_headers(user_batch_admin),
        "headers_org_admin": get_headers(user_org_admin),
        "headers_org_b": get_headers(user_org_b),
    }


def test_1_employee_a_get_employee_b_okr_success(client, authz_setup):
    """Test 1: Employee A attempting GET /okrs/{employee_b_okr_id} -> Expect 200 OK (authorization removed)."""
    headers = authz_setup["headers_emp_a"]
    okr_b_id = authz_setup["okr_b"].id

    res = client.get(f"/okrs/{okr_b_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK


def test_2_employee_a_put_employee_b_okr_success(client, authz_setup):
    """Test 2: Employee A attempting PUT /okrs/{employee_b_okr_id} -> Expect 200 OK (authorization removed)."""
    headers = authz_setup["headers_emp_a"]
    okr_b_id = authz_setup["okr_b"].id

    res = client.put(f"/okrs/{okr_b_id}", json={"objective": "Updated Objective"}, headers=headers)
    assert res.status_code == status.HTTP_200_OK


def test_3_user_in_org_a_get_org_b_okr_success(client, authz_setup):
    """Test 3: User in Org A querying OKR in Org B -> Expect 200 OK (authorization removed)."""
    headers = authz_setup["headers_emp_a"]
    okr_org_b_id = authz_setup["okr_org_b"].id

    res = client.get(f"/okrs/{okr_org_b_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK


def test_4_batch_admin_managing_okr_in_batch_success(client, authz_setup):
    """Test 4: Batch Admin managing OKR inside their batch -> Expect 200 OK."""
    headers = authz_setup["headers_batch_admin"]
    okr_b_id = authz_setup["okr_b"].id

    res = client.get(f"/okrs/{okr_b_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    res_put = client.put(f"/okrs/{okr_b_id}", json={"objective": "Updated by Batch Admin"}, headers=headers)
    assert res_put.status_code == status.HTTP_200_OK
    assert res_put.json()["objective"] == "Updated by Batch Admin"


def test_5_batch_admin_managing_okr_in_different_batch_success(client, authz_setup):
    """Test 5: Batch Admin managing OKR in a different batch -> Expect 200 OK (authorization removed)."""
    headers = authz_setup["headers_batch_admin"]
    okr_a2_id = authz_setup["okr_a2"].id

    res = client.get(f"/okrs/{okr_a2_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    res_put = client.put(f"/okrs/{okr_a2_id}", json={"objective": "Updated by Batch Admin"}, headers=headers)
    assert res_put.status_code == status.HTTP_200_OK


def test_6_org_admin_managing_any_okr_in_org_success(client, authz_setup):
    """Test 6: Org Admin managing any OKR in their org -> Expect 200 OK."""
    headers = authz_setup["headers_org_admin"]
    okr_b_id = authz_setup["okr_b"].id
    okr_a2_id = authz_setup["okr_a2"].id

    res1 = client.get(f"/okrs/{okr_b_id}", headers=headers)
    assert res1.status_code == status.HTTP_200_OK

    res2 = client.get(f"/okrs/{okr_a2_id}", headers=headers)
    assert res2.status_code == status.HTTP_200_OK

    res_put = client.put(f"/okrs/{okr_a2_id}", json={"objective": "Updated by Org Admin"}, headers=headers)
    assert res_put.status_code == status.HTTP_200_OK


def test_7_multiple_org_memberships_without_header_returns_200(client, db_session, authz_setup):
    """Test 7: User with multiple active memberships querying /okrs/ without X-Organization-ID -> Expect 200 OK."""
    fastapi_app.dependency_overrides.pop(get_current_user, None)

    # User in both Org A and Org B
    multi_user = User(username="multi_user", email="multi@test.com", password_hash=hash_password("Pass123!"), first_name="Multi", is_deleted=False)
    db_session.add(multi_user)
    db_session.commit()

    role_emp = db_session.query(Role).filter(Role.name == "EMPLOYEE").first()
    org_a = authz_setup["org_a"]
    org_b = authz_setup["org_b"]

    mem_a = OrganizationMember(user_id=multi_user.id, organization_id=org_a.id, role_id=role_emp.id, is_active=True, is_deleted=False)
    mem_b = OrganizationMember(user_id=multi_user.id, organization_id=org_b.id, role_id=role_emp.id, is_active=True, is_deleted=False)
    db_session.add_all([mem_a, mem_b])
    db_session.commit()

    token = create_access_token({"sub": str(multi_user.id), "email": multi_user.email, "username": multi_user.username})
    headers = {"Authorization": f"Bearer {token}"}

    res_no_header = client.get("/okrs/", headers=headers)
    assert res_no_header.status_code == status.HTTP_200_OK


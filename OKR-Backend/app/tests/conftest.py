"""
Shared pytest fixtures for all application test suites.

Available fixtures:
- db_session
- client
- test_user
- deleted_user
- access_token
- refresh_token
- auth_headers
- auth_jwt_client
- query_setup

Available helper functions:
- get_jwt_headers
"""

import uuid
import os
from datetime import date, datetime, UTC
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import dependencies
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.auth.password import hash_password
from app.batches.models import Batch, BatchMember, Quarter, MeetingDay, BatchStatus
from app.core.database import Base, get_db
from app.main import app as fastapi_app
from app.organizations.models import Organization
from app.organization_members.models import OrganizationMember
from app.queries.models import Query, QueryPriority, QueryStatus
from app.rbac.models import Role
from app.users.models import User

import app.users.models  # noqa
import app.organizations.models  # noqa
import app.rbac.models  # noqa
import app.batches.models  # noqa
import app.organization_members.models  # noqa
import app.my_okr.models  # noqa
import app.fogs_hurdles.models  # noqa
import app.weekly_update.models  # noqa
import app.tracker_entries.models  # noqa
import app.queries.models  # noqa
import app.query_activity.models  # noqa

import app.okr_logs.models  # noqa


# =====================================================
# Test Database (In-Memory SQLite with StaticPool)
# =====================================================

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite://")

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


# =====================================================
# Database Session
# =====================================================


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# =====================================================
# Dependency Override
# =====================================================

def override_get_current_user():
    return User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("Admin@123"),
        first_name="Admin",
        is_deleted=False,
    )


# =====================================================
# Test Client (Default with Current User Override)
# =====================================================


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[dependencies.get_current_user] = override_get_current_user

    with TestClient(fastapi_app) as client:
        yield client

    fastapi_app.dependency_overrides.clear()


# =====================================================
# JWT Authenticated Test Client
# =====================================================


@pytest.fixture(scope="function")
def auth_jwt_client(db_session):
    """TestClient that uses real token decoding against test database."""
    def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    if dependencies.get_current_user in fastapi_app.dependency_overrides:
        del fastapi_app.dependency_overrides[dependencies.get_current_user]

    with TestClient(fastapi_app) as client:
        yield client

    fastapi_app.dependency_overrides.clear()


# =====================================================
# JWT Authorization Header Helper
# =====================================================


def get_jwt_headers(user: User) -> dict:
    """Generate JWT authorization header for a user safely reading instance dict."""
    user_id = user.__dict__.get("id", getattr(user, "id", None))
    user_email = user.__dict__.get("email", getattr(user, "email", None))
    token = create_access_token({"sub": str(user_id), "email": str(user_email)})
    return {"Authorization": f"Bearer {token}"}


# =====================================================
# Test Users & Tokens
# =====================================================


@pytest.fixture
def test_user(db_session):
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("Test@123"),
        first_name="Test",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def deleted_user(db_session):
    user = User(
        id=uuid.uuid4(),
        username="deleteduser",
        email="deleted@example.com",
        password_hash=hash_password("Test@123"),
        first_name="Deleted",
        is_deleted=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def access_token(test_user):
    return create_access_token(
        {
            "sub": str(test_user.id),
            "email": test_user.email,
        }
    )


@pytest.fixture
def refresh_token(test_user):
    return create_refresh_token(
        {
            "sub": str(test_user.id),
            "email": test_user.email,
        }
    )


@pytest.fixture
def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


# =====================================================
# Complete Query Module Hierarchy Setup Fixture
# =====================================================


@pytest.fixture
def query_setup(db_session):
    """
    Sets up a complete hierarchy with:
    - 2 Organizations (org1, org2)
    - 1 Batch in org1
    - Roles: SUPER_ADMIN, ORG_ADMIN, BATCH_ADMIN, EMPLOYEE
    - Users: super_admin, org_admin, batch_admin, emp1, emp2, unrelated_emp, inactive_user
    - Organization Memberships
    """
    # Organizations
    existing_orgs = {o.name: o for o in db_session.query(Organization).all()}
    org1 = existing_orgs.get("Query Test Org 1") or Organization(name="Query Test Org 1", is_deleted=False)
    org2 = existing_orgs.get("Query Test Org 2", None)
    if not org2:
        org2 = Organization(name="Query Test Org 2", is_deleted=False)

    orgs_to_add = [o for o in [org1, org2] if o not in db_session]
    if orgs_to_add:
        db_session.add_all(orgs_to_add)
        db_session.flush()

    # Batch
    batch1 = db_session.query(Batch).filter(Batch.name == "Query Batch Q1 2026").first()
    if not batch1:
        batch1 = Batch(
            name="Query Batch Q1 2026",
            year=2026,
            quarter=Quarter.JFM,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            meeting_day=MeetingDay.MONDAY,
            status=BatchStatus.ACTIVE,
            organization_id=org1.id,
            is_deleted=False,
        )
        db_session.add(batch1)
        db_session.flush()

    # Roles
    existing_roles = {r.name: r for r in db_session.query(Role).all()}
    role_super = existing_roles.get("SUPER_ADMIN") or Role(name="SUPER_ADMIN", description="Super Admin")
    role_org_admin = existing_roles.get("ORG_ADMIN") or Role(name="ORG_ADMIN", description="Org Admin")
    role_batch_admin = existing_roles.get("BATCH_ADMIN") or Role(name="BATCH_ADMIN", description="Batch Admin")
    role_emp = existing_roles.get("EMPLOYEE") or Role(name="EMPLOYEE", description="Employee")

    roles_to_add = [r for r in [role_super, role_org_admin, role_batch_admin, role_emp] if r not in db_session]
    if roles_to_add:
        db_session.add_all(roles_to_add)
        db_session.flush()

    # Users
    existing_users = {u.username: u for u in db_session.query(User).all()}

    super_admin = existing_users.get("q_superadmin")
    if not super_admin:
        super_admin = User(
            id=uuid.uuid4(), username="q_superadmin", email="q_superadmin@test.com", password_hash="hash", first_name="Super", last_name="Admin", is_deleted=False, is_active=True
        )
        setattr(super_admin, "is_superuser", True)

    org_admin = existing_users.get("q_orgadmin") or User(
        id=uuid.uuid4(), username="q_orgadmin", email="q_orgadmin@test.com", password_hash="hash", first_name="Org", last_name="Admin", is_deleted=False, is_active=True
    )

    batch_admin = existing_users.get("q_batchadmin") or User(
        id=uuid.uuid4(), username="q_batchadmin", email="q_batchadmin@test.com", password_hash="hash", first_name="Batch", last_name="Admin", is_deleted=False, is_active=True
    )

    emp1 = existing_users.get("q_emp1") or User(
        id=uuid.uuid4(), username="q_emp1", email="q_emp1@test.com", password_hash="hash", first_name="Emp", last_name="One", is_deleted=False, is_active=True
    )

    emp2 = existing_users.get("q_emp2") or User(
        id=uuid.uuid4(), username="q_emp2", email="q_emp2@test.com", password_hash="hash", first_name="Emp", last_name="Two", is_deleted=False, is_active=True
    )

    unrelated_emp = existing_users.get("q_unrelated") or User(
        id=uuid.uuid4(), username="q_unrelated", email="q_unrelated@test.com", password_hash="hash", first_name="Unrelated", last_name="User", is_deleted=False, is_active=True
    )

    inactive_user = existing_users.get("q_inactive") or User(
        id=uuid.uuid4(), username="q_inactive", email="q_inactive@test.com", password_hash="hash", first_name="Inactive", last_name="User", is_deleted=False, is_active=False
    )

    no_membership_user = existing_users.get("q_nomember") or User(
        id=uuid.uuid4(), username="q_nomember", email="q_nomember@test.com", password_hash="hash", first_name="NoMember", last_name="User", is_deleted=False, is_active=True
    )

    users_to_add = [
        u for u in [super_admin, org_admin, batch_admin, emp1, emp2, unrelated_emp, inactive_user, no_membership_user]
        if u not in db_session
    ]
    if users_to_add:
        db_session.add_all(users_to_add)
        db_session.flush()

    # Memberships
    existing_mems = {(m.organization_id, m.user_id): m for m in db_session.query(OrganizationMember).all()}

    om_super = existing_mems.get((org1.id, super_admin.id)) or OrganizationMember(
        organization_id=org1.id, user_id=super_admin.id, role_id=role_super.id, is_deleted=False, is_active=True
    )
    om_org_admin = existing_mems.get((org1.id, org_admin.id)) or OrganizationMember(
        organization_id=org1.id, user_id=org_admin.id, role_id=role_org_admin.id, is_deleted=False, is_active=True
    )
    om_batch_admin = existing_mems.get((org1.id, batch_admin.id)) or OrganizationMember(
        organization_id=org1.id, user_id=batch_admin.id, role_id=role_batch_admin.id, is_deleted=False, is_active=True
    )
    om_emp1 = existing_mems.get((org1.id, emp1.id)) or OrganizationMember(
        organization_id=org1.id, user_id=emp1.id, role_id=role_emp.id, is_deleted=False, is_active=True
    )
    om_emp2 = existing_mems.get((org1.id, emp2.id)) or OrganizationMember(
        organization_id=org1.id, user_id=emp2.id, role_id=role_emp.id, is_deleted=False, is_active=True
    )
    om_unrelated = existing_mems.get((org2.id, unrelated_emp.id)) or OrganizationMember(
        organization_id=org2.id, user_id=unrelated_emp.id, role_id=role_emp.id, is_deleted=False, is_active=True
    )
    om_inactive = existing_mems.get((org1.id, inactive_user.id)) or OrganizationMember(
        organization_id=org1.id, user_id=inactive_user.id, role_id=role_emp.id, is_deleted=False, is_active=False
    )

    mems_to_add = [
        m for m in [om_super, om_org_admin, om_batch_admin, om_emp1, om_emp2, om_unrelated, om_inactive]
        if m not in db_session
    ]
    if mems_to_add:
        db_session.add_all(mems_to_add)
        db_session.flush()

    # Batch Memberships
    existing_bms = {(bm.batch_id, bm.user_id): bm for bm in db_session.query(BatchMember).all()}
    bm_batch_admin = existing_bms.get((batch1.id, batch_admin.id)) or BatchMember(
        batch_id=batch1.id, user_id=batch_admin.id, role_id=role_batch_admin.id, is_deleted=False, is_active=True
    )
    bm_emp1 = existing_bms.get((batch1.id, emp1.id)) or BatchMember(
        batch_id=batch1.id, user_id=emp1.id, role_id=role_emp.id, is_deleted=False, is_active=True
    )
    bms_to_add = [bm for bm in [bm_batch_admin, bm_emp1] if bm not in db_session]
    if bms_to_add:
        db_session.add_all(bms_to_add)
        db_session.flush()

    return {
        "org1": org1,
        "org2": org2,
        "batch1": batch1,
        "super_admin": super_admin,
        "org_admin": org_admin,
        "batch_admin": batch_admin,
        "emp1": emp1,
        "emp2": emp2,
        "unrelated_emp": unrelated_emp,
        "inactive_user": inactive_user,
        "no_membership_user": no_membership_user,
    }

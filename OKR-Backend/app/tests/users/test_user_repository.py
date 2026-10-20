"""
Tests for User repository layer.
"""

import uuid
import pytest

from app.users import repository
from app.users.schemas import UserCreate, UserUpdate


def create_sample_user_create_data(username="repo_user", email="repo@example.com", org_id=None, role_id=None):
    return UserCreate(
        username=username,
        email=email,
        password="Password@123",
        first_name="Repo",
        last_name="Test",
        phone="1234567890",
        designation="Tester",
        description="Repo test user",
        organization_id=org_id or uuid.uuid4(),
        role_id=role_id or uuid.uuid4(),
    )


def test_create_user_repository(db_session):
    """
    Test creating a user directly via repository layer.
    """
    user_data = create_sample_user_create_data()
    hashed_pwd = "hashed_secret_password"

    user = repository.create_user(
        db=db_session,
        user_data=user_data,
        password_hash=hashed_pwd,
    )

    assert user.id is not None
    assert user.username == "repo_user"
    assert user.email == "repo@example.com"
    assert user.password_hash == hashed_pwd
    assert user.first_name == "Repo"
    assert user.is_deleted is False


def test_get_user_by_id_repository(db_session, test_user):
    """
    Test getting a user by ID via repository.
    """
    fetched = repository.get_user_by_id(db_session, test_user.id)
    assert fetched is not None
    assert fetched.id == test_user.id

    # Non-existent ID returns None
    non_existent = repository.get_user_by_id(db_session, uuid.uuid4())
    assert non_existent is None


def test_get_user_by_username_repository(db_session, test_user):
    """
    Test getting user by username.
    """
    fetched = repository.get_user_by_username(db_session, test_user.username)
    assert fetched is not None
    assert fetched.id == test_user.id

    # Non-existent username returns None
    assert repository.get_user_by_username(db_session, "non_existent_user") is None


def test_get_user_by_email_repository(db_session, test_user):
    """
    Test getting user by email.
    """
    fetched = repository.get_user_by_email(db_session, test_user.email)
    assert fetched is not None
    assert fetched.id == test_user.id

    # Non-existent email returns None
    assert repository.get_user_by_email(db_session, "fake@example.com") is None


def test_get_users_repository_pagination_and_search(db_session):
    """
    Test listing users with pagination and search parameters.
    """
    user1 = repository.create_user(
        db_session,
        create_sample_user_create_data("alpha", "alpha@test.com"),
        "hash1",
    )
    user2 = repository.create_user(
        db_session,
        create_sample_user_create_data("beta", "beta@test.com"),
        "hash2",
    )

    users, total = repository.get_users(db_session, page=1, size=10)
    assert total >= 2

    # Search filter
    users, total = repository.get_users(db_session, page=1, size=10, search="alpha")
    assert total == 1
    assert users[0].id == user1.id


def test_update_user_repository(db_session, test_user):
    """
    Test updating user fields via repository.
    """
    update_data = UserUpdate(first_name="NewRepoName", designation="Lead Tester")
    updated = repository.update_user(db_session, test_user, update_data)

    assert updated.first_name == "NewRepoName"
    assert updated.designation == "Lead Tester"


def test_delete_user_repository(db_session, test_user):
    """
    Test soft-deleting user via repository.
    """
    deleted = repository.delete_user(db_session, test_user)

    assert deleted.is_deleted is True
    assert repository.get_user_by_id(db_session, test_user.id) is None


def test_get_users_by_organization_repository(db_session, test_user):
    """
    Test getting users belonging to an organization.
    """
    from app.organizations.models import Organization
    from app.organization_members.models import OrganizationMember
    from app.rbac.models import Role

    org = Organization(name="Test Org Repo")
    role = Role(name="Member Role", description="Member")
    db_session.add_all([org, role])
    db_session.commit()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=test_user.id,
        role_id=role.id,
    )
    db_session.add(member)
    db_session.commit()

    users, total = repository.get_users_by_organization(
        db_session,
        organization_id=org.id,
        page=1,
        size=10,
    )

    assert total == 1
    assert users[0].id == test_user.id


"""
Tests for User service layer.
"""

import uuid
from unittest.mock import patch

import pytest

from app.auth.password import verify_password
from app.common.exceptions import (
    OrganizationNotFoundException,
    RoleNotFoundException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User
from app.users.schemas import UserCreate, UserUpdate
from app.users.service import (
    create_user_service,
    delete_user,
    get_user_by_id,
    get_users,
    get_users_by_organization_service,
    update_user,
)


@pytest.fixture
def test_organization(db_session):
    org = Organization(
        id=uuid.uuid4(),
        name=f"Test Organization {uuid.uuid4()}",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_role(db_session):
    role = Role(
        id=uuid.uuid4(),
        name=f"Developer {uuid.uuid4()}",
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


def create_test_user_data(
    organization_id: uuid.UUID,
    role_id: uuid.UUID,
    username: str = "anand",
    email: str = "anand@test.com",
):
    return UserCreate(
        username=username,
        email=email,
        password="Password@123",
        first_name="Anand",
        last_name="Kumar",
        designation="Developer",
        description="Backend Developer",
        organization_id=organization_id,
        role_id=role_id,
    )


# ==========================================================
# Create User Tests
# ==========================================================


def test_create_user_success(db_session, test_organization, test_role):
    """
    User and OrganizationMember should be created successfully in one transaction.
    """

    org_id = test_organization.id
    user_data = create_test_user_data(
        organization_id=org_id,
        role_id=test_role.id,
    )

    user = create_user_service(
        db=db_session,
        user_data=user_data,
    )

    assert user.id is not None
    assert user.username == "anand"
    assert user.email == "anand@test.com"

    member = (
        db_session.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )

    assert member is not None
    assert member.organization_id == org_id
    assert member.user_id == user.id
    assert member.role_id == test_role.id


def test_password_is_hashed(db_session, test_organization, test_role):
    """
    Password should not be stored as plain text.
    """

    org_id = test_organization.id
    role_id = test_role.id

    user_data = create_test_user_data(
        organization_id=org_id,
        role_id=role_id,
    )

    user = create_user_service(
        db=db_session,
        user_data=user_data,
    )

    assert user.password_hash != "Password@123"

    assert verify_password(
        "Password@123",
        user.password_hash,
    )


# ==========================================================
# Invalid Ref / Duplicate / Rollback Tests
# ==========================================================


def test_create_user_invalid_organization(db_session, test_role):
    """
    Creating user with non-existent organization_id should fail and leave no User in DB.
    """

    invalid_org_id = uuid.uuid4()
    user_data = create_test_user_data(
        organization_id=invalid_org_id,
        role_id=test_role.id,
        username="invalid_org_user",
        email="invalidorg@test.com",
    )

    with pytest.raises(OrganizationNotFoundException):
        create_user_service(
            db=db_session,
            user_data=user_data,
        )

    user = (
        db_session.query(User)
        .filter(User.username == "invalid_org_user")
        .first()
    )
    assert user is None


def test_create_user_invalid_role(db_session, test_organization):
    """
    Creating user with non-existent role_id should fail and leave no User in DB.
    """

    invalid_role_id = uuid.uuid4()
    user_data = create_test_user_data(
        organization_id=test_organization.id,
        role_id=invalid_role_id,
        username="invalid_role_user",
        email="invalidrole@test.com",
    )

    with pytest.raises(RoleNotFoundException):
        create_user_service(
            db=db_session,
            user_data=user_data,
        )

    user = (
        db_session.query(User)
        .filter(User.username == "invalid_role_user")
        .first()
    )
    assert user is None


def test_duplicate_username(db_session, test_organization, test_role):
    """
    Duplicate username should raise UserAlreadyExistsException.
    """

    user_data = create_test_user_data(
        organization_id=test_organization.id,
        role_id=test_role.id,
    )

    create_user_service(
        db=db_session,
        user_data=user_data,
    )

    with pytest.raises(UserAlreadyExistsException):
        create_user_service(
            db=db_session,
            user_data=create_test_user_data(
                organization_id=test_organization.id,
                role_id=test_role.id,
                username="anand",
                email="another@test.com",
            ),
        )


def test_duplicate_email(db_session, test_organization, test_role):
    """
    Duplicate email should raise UserAlreadyExistsException.
    """

    user_data = create_test_user_data(
        organization_id=test_organization.id,
        role_id=test_role.id,
    )

    create_user_service(
        db=db_session,
        user_data=user_data,
    )

    with pytest.raises(UserAlreadyExistsException):
        create_user_service(
            db=db_session,
            user_data=create_test_user_data(
                organization_id=test_organization.id,
                role_id=test_role.id,
                username="another",
                email="anand@test.com",
            ),
        )


def test_organization_user_listing(db_session, test_organization, test_role):
    """
    Newly created user should appear in get_users_by_organization_service.
    """

    org_id = test_organization.id
    role_id = test_role.id

    user_data = create_test_user_data(
        organization_id=org_id,
        role_id=role_id,
        username="org_member_user",
        email="orgmember@test.com",
    )

    user = create_user_service(
        db=db_session,
        user_data=user_data,
    )

    users, total = get_users_by_organization_service(
        db=db_session,
        organization_id=org_id,
    )

    assert total == 1
    assert users[0].id == user.id
    assert users[0].role is not None
    assert users[0].role.id == test_role.id
    assert users[0].role.name == test_role.name


def test_transaction_rollback_on_member_creation_failure(
    db_session, test_organization, test_role
):
    """
    If OrganizationMember creation fails after User flush, the User creation must also be rolled back.
    """

    user_data = create_test_user_data(
        organization_id=test_organization.id,
        role_id=test_role.id,
        username="rollback_user",
        email="rollback@test.com",
    )

    with patch(
        "app.users.service.create_organization_member",
        side_effect=RuntimeError("Simulated OrganizationMember creation failure"),
    ):
        with pytest.raises(RuntimeError, match="Simulated OrganizationMember creation failure"):
            create_user_service(
                db=db_session,
                user_data=user_data,
            )

    user = (
        db_session.query(User)
        .filter(User.username == "rollback_user")
        .first()
    )
    assert user is None


# ==========================================================
# Read, Update, Delete Service Tests
# ==========================================================


def test_get_user_by_id_success(db_session, test_user):
    """get_user_by_id should return user object."""

    user = get_user_by_id(db_session, test_user.id)

    assert user.id == test_user.id


def test_get_user_by_id_not_found(db_session):
    """Non-existent user_id should raise UserNotFoundException."""

    with pytest.raises(UserNotFoundException):
        get_user_by_id(db_session, uuid.uuid4())


def test_get_users_service(db_session, test_user):
    """get_users should return user list and count."""

    users, total = get_users(db_session, page=1, size=10, search="test")

    assert total >= 1
    assert len(users) >= 1


def test_update_user_service(db_session, test_user):
    """update_user should modify user fields."""

    updated = update_user(
        db_session,
        test_user.id,
        UserUpdate(first_name="UpdatedName"),
    )

    assert updated.first_name == "UpdatedName"


def test_delete_user_service(db_session, test_user):
    """delete_user should set is_deleted to True."""

    result = delete_user(db_session, test_user.id)

    assert result is True

    with pytest.raises(UserNotFoundException):
        get_user_by_id(db_session, test_user.id)


def test_get_users_service_with_search_filter(
    db_session, test_organization, test_role
):
    """
    Verify search parameter filters users by ILIKE matching on first_name/username/email.
    """

    user_data = create_test_user_data(
        organization_id=test_organization.id,
        role_id=test_role.id,
        username="search_user",
        email="searchable@test.com",
    )
    user_data.first_name = "UniqueSearchName"
    create_user_service(db_session, user_data)

    users, total = get_users(db_session, page=1, size=10, search="UniqueSearchName")

    assert total == 1
    assert users[0].first_name == "UniqueSearchName"


def test_update_user_duplicate_username(db_session, test_organization, test_role):
    """Updating user to existing username of another user raises UserAlreadyExistsException."""

    user1 = create_user_service(
        db_session,
        create_test_user_data(
            organization_id=test_organization.id,
            role_id=test_role.id,
            username="akash",
            email="akash@test.com",
        ),
    )

    user2 = create_user_service(
        db_session,
        create_test_user_data(
            organization_id=test_organization.id,
            role_id=test_role.id,
            username="rohan",
            email="rohan@test.com",
        ),
    )

    with pytest.raises(UserAlreadyExistsException):
        update_user(
            db_session,
            user2.id,
            UserUpdate(username="akash"),
        )

    updated_user2 = update_user(
        db_session,
        user2.id,
        UserUpdate(username="rohan_new"),
    )
    assert updated_user2.username == "rohan_new"


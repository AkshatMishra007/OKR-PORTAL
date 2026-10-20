"""
Tests for User Pydantic schemas.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.users.schemas import (
    UserCreate,
    UserListItem,
    UserResponse,
    UserUpdate,
)

# ==========================================================
# UserCreate Tests
# ==========================================================


def test_user_create_valid_data():
    """
    Valid user creation data should pass validation.
    """

    user = UserCreate(
        username="anand",
        email="anand@test.com",
        password="Password@123",
        first_name="Anand",
        last_name="Kumar",
        designation="Developer",
        organization_id=uuid4(),
        role_id=uuid4(),
    )

    assert user.username == "anand"
    assert user.email == "anand@test.com"
    assert user.password == "Password@123"


def test_user_create_invalid_email():
    """
    Invalid email should fail validation.
    """

    with pytest.raises(ValidationError):

        UserCreate(
            username="anand",
            email="invalid-email",
            password="Password@123",
            first_name="Anand",
            organization_id=uuid4(),
            role_id=uuid4(),
        )


def test_user_create_short_username():
    """
    Username shorter than minimum length should fail.
    """

    with pytest.raises(ValidationError):

        UserCreate(
            username="ab",
            email="anand@test.com",
            password="Password@123",
            first_name="Anand",
            organization_id=uuid4(),
            role_id=uuid4(),
        )


def test_user_create_short_password():
    """
    Password shorter than 8 characters should fail.
    """

    with pytest.raises(ValidationError):

        UserCreate(
            username="anand",
            email="anand@test.com",
            password="123",
            first_name="Anand",
            organization_id=uuid4(),
            role_id=uuid4(),
        )


def test_user_create_optional_fields():
    """
    Optional fields should accept None.
    """

    user = UserCreate(
        username="anand",
        email="anand@test.com",
        password="Password@123",
        first_name="Anand",
        organization_id=uuid4(),
        role_id=uuid4(),
    )

    assert user.last_name is None
    assert user.phone is None
    assert user.designation is None


# ==========================================================
# UserUpdate Tests
# ==========================================================


def test_user_update_partial_data():
    """
    User update should allow partial updates.
    """

    user = UserUpdate(designation="Senior Developer")

    assert user.designation == "Senior Developer"
    assert user.first_name is None


def test_user_update_does_not_require_password():
    user = UserUpdate(designation="Senior Developer")

    assert user.password is None
    assert "password" not in user.model_dump(exclude_unset=True)


def test_user_update_empty_data():
    """
    Empty update object should be allowed.
    """

    user = UserUpdate()

    assert user.first_name is None
    assert user.designation is None


# ==========================================================
# Response Schema Tests
# ==========================================================


def test_user_response_fields():

    from datetime import UTC, datetime
    from uuid import uuid4

    user = UserResponse(
        id=uuid4(),
        username="anand",
        email="anand@test.com",
        first_name="Anand",
        last_name="Kumar",
        phone=None,
        designation="Developer",
        description=None,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert user.username == "anand"
    assert user.is_active is True


def test_user_list_item_fields():

    from datetime import UTC, datetime
    from uuid import uuid4
    from app.users.schemas import OrganizationMembershipResponse, RoleNestedResponse

    org_id = uuid4()
    membership = OrganizationMembershipResponse(
        organization_id=org_id,
        organization_name="Ace",
        role=RoleNestedResponse(id=uuid4(), name="ORG_ADMIN", description="Org Admin"),
        batch_id=None,
    )

    user = UserListItem(
        id=uuid4(),
        username="anand",
        email="anand@test.com",
        first_name="Anand",
        last_name="Kumar",
        phone="9876543210",
        designation="Developer",
        description="Senior Developer",
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        organization_memberships=[membership],
    )

    assert user.username == "anand"
    assert user.designation == "Developer"
    assert user.phone == "9876543210"
    assert user.description == "Senior Developer"
    assert len(user.organization_memberships) == 1
    assert user.organization_memberships[0].organization_name == "Ace"
    assert user.organization_memberships[0].role.name == "ORG_ADMIN"
    assert user.organization_memberships[0].batch_id is None

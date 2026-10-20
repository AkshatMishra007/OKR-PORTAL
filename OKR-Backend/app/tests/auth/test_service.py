"""
Unit tests for authentication service.
"""

import pytest

from app.auth.password import hash_password
from app.auth.service import (
    authenticate_user,
    login,
    logout,
)
from app.common.exceptions import (
    InvalidCredentialsException,
)
from app.users.models import User

# =====================================================
# authenticate_user()
# =====================================================


def test_authenticate_user_with_email(db_session):
    """User should authenticate using email."""

    user = User(
        username="john_email",
        email="john_email@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    authenticated = authenticate_user(
        db=db_session,
        username_or_email="john_email@test.com",
        password="Password@123",
    )

    assert authenticated.email == user.email


def test_authenticate_user_with_username(db_session):
    """User should authenticate using username."""

    user = User(
        username="john_uname",
        email="john_uname@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    authenticated = authenticate_user(
        db=db_session,
        username_or_email="john_uname",
        password="Password@123",
    )

    assert authenticated.username == user.username


def test_authenticate_user_invalid_email(db_session):
    """Unknown email should raise InvalidCredentialsException."""

    with pytest.raises(InvalidCredentialsException):
        authenticate_user(
            db=db_session,
            username_or_email="missing@test.com",
            password="Password@123",
        )


def test_authenticate_user_invalid_username(db_session):
    """Unknown username should raise InvalidCredentialsException."""

    with pytest.raises(InvalidCredentialsException):
        authenticate_user(
            db=db_session,
            username_or_email="missing_user",
            password="Password@123",
        )


def test_authenticate_user_wrong_password(db_session):
    """Wrong password should raise InvalidCredentialsException."""

    user = User(
        username="john_wrongpass",
        email="john_wrongpass@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    with pytest.raises(InvalidCredentialsException):
        authenticate_user(
            db=db_session,
            username_or_email="john_wrongpass@test.com",
            password="WrongPassword",
        )


def test_authenticate_user_deleted_user(db_session):
    """Deleted users should not authenticate."""

    user = User(
        username="john_deleted",
        email="john_deleted@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=True,
    )

    db_session.add(user)
    db_session.commit()

    with pytest.raises(InvalidCredentialsException):
        authenticate_user(
            db=db_session,
            username_or_email="john_deleted@test.com",
            password="Password@123",
        )


def test_authenticate_user_is_case_sensitive(db_session):
    """Username lookup should remain case-sensitive."""

    user = User(
        username="JohnCase",
        email="john_case@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    with pytest.raises(InvalidCredentialsException):
        authenticate_user(
            db=db_session,
            username_or_email="johncase",
            password="Password@123",
        )


# =====================================================
# login()
# =====================================================


def test_login_returns_tokens(db_session):
    """Login should return both JWT tokens."""

    user = User(
        username="john_login1",
        email="john_login1@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    response = login(
        db=db_session,
        username_or_email="john_login1@test.com",
        password="Password@123",
    )

    assert "access_token" in response
    assert "refresh_token" in response
    assert response["token_type"] == "bearer"


def test_login_returns_non_empty_tokens(db_session):
    """Returned JWTs should not be empty."""

    user = User(
        username="john_login2",
        email="john_login2@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    response = login(
        db=db_session,
        username_or_email="john_login2@test.com",
        password="Password@123",
    )

    assert response["access_token"]
    assert response["refresh_token"]


def test_login_invalid_password(db_session):
    """Invalid password should propagate InvalidCredentialsException."""

    user = User(
        username="john_login3",
        email="john_login3@test.com",
        password_hash=hash_password("Password@123"),
        first_name="John",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()

    with pytest.raises(InvalidCredentialsException):
        login(
            db=db_session,
            username_or_email="john_login3@test.com",
            password="WrongPassword",
        )


def test_login_unknown_user(db_session):
    """Unknown user should not login."""

    with pytest.raises(InvalidCredentialsException):
        login(
            db=db_session,
            username_or_email="ghost@test.com",
            password="Password@123",
        )


def test_logout_service():
    """Logout service should return success dict."""

    user = User(
        username="logout_user",
        email="logout@test.com",
        first_name="Logout",
    )
    result = logout(user)

    assert result == {"message": "Successfully logged out."}

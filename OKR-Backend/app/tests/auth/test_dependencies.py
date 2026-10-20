"""
Unit tests for authentication dependencies.
"""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token

# =====================================================
# Success Cases
# =====================================================


def test_get_current_user_success(
    db_session,
    test_user,
    access_token,
):
    """
    A valid access token should return the authenticated user.
    """

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token,
    )

    user = get_current_user(
        credentials=credentials,
        db=db_session,
    )

    assert user.id == test_user.id
    assert user.email == test_user.email
    assert user.username == test_user.username


# =====================================================
# Invalid Token
# =====================================================


def test_get_current_user_invalid_token(
    db_session,
):
    """
    Invalid JWT should return HTTP 401.
    """

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token",
    )

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )

    assert exc.value.status_code == 401


# =====================================================
# Refresh Token
# =====================================================


def test_get_current_user_rejects_refresh_token(
    db_session,
    refresh_token,
):
    """
    Refresh token cannot authenticate a user.
    """

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=refresh_token,
    )

    with pytest.raises(HTTPException) as exc:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )

    assert exc.value.status_code == 401


# =====================================================
# Missing Subject
# =====================================================


def test_get_current_user_missing_subject(
    db_session,
):
    """
    Token without sub claim should be rejected.
    """

    token = create_access_token(
        {
            "email": "test@test.com",
        }
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException):
        get_current_user(
            credentials=credentials,
            db=db_session,
        )


# =====================================================
# Invalid UUID
# =====================================================


def test_get_current_user_invalid_uuid(
    db_session,
):
    """
    Subject must be a valid UUID.
    """

    token = create_access_token(
        {
            "sub": "not-a-valid-uuid",
            "email": "test@test.com",
        }
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException):
        get_current_user(
            credentials=credentials,
            db=db_session,
        )


# =====================================================
# User Doesn't Exist
# =====================================================


def test_get_current_user_user_not_found(
    db_session,
):
    """
    Valid token for non-existing user should return 401.
    """

    token = create_access_token(
        {
            "sub": str(uuid4()),
            "email": "ghost@test.com",
        }
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException):
        get_current_user(
            credentials=credentials,
            db=db_session,
        )


# =====================================================
# Deleted User
# =====================================================


def test_get_current_user_deleted_user(
    db_session,
    deleted_user,
):
    """
    Deleted users should not authenticate.
    """

    token = create_access_token(
        {
            "sub": str(deleted_user.id),
            "email": deleted_user.email,
        }
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException):
        get_current_user(
            credentials=credentials,
            db=db_session,
        )


# =====================================================
# Missing Token Type
# =====================================================


def test_get_current_user_missing_token_type(
    db_session,
):
    """
    Token without token_type should be rejected.
    """

    from jose import jwt

    from app.core.config import settings

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "email": "test@test.com",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException):
        get_current_user(
            credentials=credentials,
            db=db_session,
        )


# =====================================================
# Wrong Token Type
# =====================================================


def test_get_current_user_wrong_token_type(
    db_session,
):
    """
    Token type other than access should be rejected.
    """

    from jose import jwt

    from app.core.config import settings

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "email": "test@test.com",
            "token_type": "admin",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(HTTPException):
        get_current_user(
            credentials=credentials,
            db=db_session,
        )


# =====================================================
# Empty Token
# =====================================================


def test_get_current_user_empty_token(
    db_session,
):
    """
    Empty bearer token should return 401.
    """

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="",
    )

    with pytest.raises(HTTPException):
        get_current_user(
            credentials=credentials,
            db=db_session,
        )

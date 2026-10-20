"""
Authentication service layer.

Responsibilities:
- Authenticate users.
- Verify credentials.
- Generate JWT tokens.

This layer does not:
- Handle HTTP requests.
- Define API routes.
- Perform authorization.
"""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.auth.password import verify_password
from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
)
from app.common.exceptions import InvalidCredentialsException
from app.users.models import User

# =====================================================
# Authenticate User
# =====================================================


def authenticate_user(
    db: Session,
    username_or_email: str,
    password: str,
) -> User:
    """
    Authenticate a user using username or email and password.
    """

    user = (
        db.query(User)
        .filter(
            or_(
                User.email == username_or_email,
                User.username == username_or_email,
            ),
            User.is_deleted.is_(False),
        )
        .first()
    )

    if not user:
        raise InvalidCredentialsException("Invalid email or password.")

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise InvalidCredentialsException("Invalid email or password.")

    return user


# =====================================================
# Login
# =====================================================


def login(
    db: Session,
    username_or_email: str,
    password: str,
) -> dict:
    """
    Authenticate user and generate JWT tokens.
    """

    user = authenticate_user(
        db=db,
        username_or_email=username_or_email,
        password=password,
    )

    claims = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
    }

    return {
        "access_token": create_access_token(claims),
        "refresh_token": create_refresh_token(claims),
        "token_type": "bearer",
    }


def login_service(
    db: Session,
    login_data: LoginRequest,
) -> LoginResponse:
    """
    Authenticate the user and generate JWT tokens.
    """

    res = login(
        db=db,
        username_or_email=login_data.username_or_email,
        password=login_data.password,
    )

    return LoginResponse(**res)


# =====================================================
# Logout
# =====================================================


def logout(
    current_user: User,
) -> dict:
    """
    Logout the authenticated user.

    Currently this is a stateless logout.
    Refresh-token invalidation will be added later.
    """

    _ = current_user

    return {
        "message": "Successfully logged out.",
    }


def logout_service(
    current_user: User,
) -> LogoutResponse:
    """
    Logout the authenticated user.
    """

    res = logout(current_user)

    return LogoutResponse(**res)

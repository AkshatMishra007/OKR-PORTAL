"""
Authentication routes.

Responsibilities:
- Handle authentication HTTP requests.
- Validate request data.
- Return authentication responses.

This layer does not:
- Contain authentication logic.
- Query the database directly.
- Create JWT tokens.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
)
from app.auth.service import (
    login_service,
    logout_service,
)
from app.core.database import get_db
from app.users.models import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =====================================================
# Login
# =====================================================


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return JWT tokens.
    """

    return login_service(
        db=db,
        login_data=login_data,
    )


# =====================================================
# Current User
# =====================================================


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
    }


# =====================================================
# Logout
# =====================================================


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout the authenticated user.
    """

    return logout_service(current_user)

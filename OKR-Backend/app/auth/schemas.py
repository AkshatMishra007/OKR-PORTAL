from pydantic import BaseModel

from app.common.types import NonEmptyStr

# =====================================================
# Login Request
# =====================================================


class LoginRequest(BaseModel):
    """
    User login credentials.

    User can login using:
    - email
    - username
    """

    username_or_email: NonEmptyStr
    password: NonEmptyStr


# =====================================================
# Login Response
# =====================================================


class LoginResponse(BaseModel):
    """
    JWT token response.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# =====================================================
# Logout Response
# =====================================================


class LogoutResponse(BaseModel):
    """
    Logout response.
    """

    message: str

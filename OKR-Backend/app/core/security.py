"""
JWT security utilities.

This module is responsible for:
- Creating access tokens
- Creating refresh tokens
- Decoding JWT tokens
- Validating token types

Business logic should not be placed here.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(payload: dict) -> str:
    """
    Generate JWT access token.
    """

    data = payload.copy()

    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    data.update(
        {
            "exp": expire,
            "token_type": "access",
        }
    )

    return jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(payload: dict) -> str:
    """
    Generate JWT refresh token.
    """

    data = payload.copy()

    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    data.update(
        {
            "exp": expire,
            "token_type": "refresh",
        }
    )

    return jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload

    except JWTError:
        raise ValueError("Invalid or expired token")


def verify_token_type(
    payload: dict,
    expected_type: str,
) -> bool:
    """
    Verify token type.
    """

    token_type = payload.get("token_type")

    if token_type != expected_type:
        raise ValueError("Invalid token type")

    return True

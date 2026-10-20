"""
JWT utilities for the authentication module.

Responsibilities:
- Create access tokens
- Create refresh tokens
- Decode JWT tokens
- Validate token types

This module does not perform authentication or authorization.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import jwt

from app.core.config import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _create_token(
    claims: dict[str, Any],
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """
    Create and sign a JWT token.

    Args:
        claims: Custom JWT claims.
        expires_delta: Token lifetime.
        token_type: access or refresh.

    Returns:
        Encoded JWT string.
    """

    now = datetime.now(UTC)

    token_claims = claims.copy()

    token_claims.update(
        {
            "iat": now,
            "exp": now + expires_delta,
            "jti": str(uuid4()),
            "token_type": token_type,
        }
    )

    return jwt.encode(
        token_claims,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_access_token(
    claims: dict[str, Any],
) -> str:
    """
    Create a short-lived access token.
    """

    return _create_token(
        claims=claims,
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
        token_type=ACCESS_TOKEN_TYPE,
    )


def create_refresh_token(
    claims: dict[str, Any],
) -> str:
    """
    Create a long-lived refresh token.
    """

    return _create_token(
        claims=claims,
        expires_delta=timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
        token_type=REFRESH_TOKEN_TYPE,
    )


def decode_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        JWTError: If the token is invalid or expired.
    """

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


def verify_token_type(
    claims: dict[str, Any],
    expected_type: str,
) -> None:
    """
    Validate the token type.

    Raises:
        ValueError: If the token type is incorrect.
    """

    token_type = claims.get("token_type")

    if token_type != expected_type:
        raise ValueError("Invalid token type.")

"""
Authentication dependencies.

Responsibilities:
- Extract JWT from Authorization header.
- Decode and validate JWT.
- Verify token type.
- Return authenticated user.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError
from sqlalchemy.orm import Session, joinedload

from app.auth.jwt import (
    ACCESS_TOKEN_TYPE,
    decode_token,
    verify_token_type,
)
from app.core.database import get_db
from app.organization_members.models import OrganizationMember
from app.users.models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if not credentials or not credentials.credentials:
        raise credentials_exception

    try:
        token = credentials.credentials

        claims = decode_token(token)

        verify_token_type(
            claims,
            ACCESS_TOKEN_TYPE,
        )

        subject = claims.get("sub")

        if not subject:
            raise credentials_exception

        user = (
            db.query(User)
            .options(
                joinedload(User.organization_members).joinedload(OrganizationMember.organization),
                joinedload(User.organization_members).joinedload(OrganizationMember.role),
            )
            .filter(
                User.id == UUID(subject),
                User.is_deleted.is_(False),
                User.is_active.is_not(False),
            )
            .first()
        )

        if not user or getattr(user, "is_active", True) is False:
            raise credentials_exception

        return user

    except (JWTError, ValueError):
        raise credentials_exception

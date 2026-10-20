"""
User Pydantic schemas.

Responsibilities:
- Validate incoming user data.
- Define API response formats.
- Hide internal database fields.
"""

from datetime import datetime
from uuid import UUID

from typing import Any
from pydantic import BaseModel, EmailStr, Field, model_validator

# ==========================================================
# Base Schema
# ==========================================================


class UserBase(BaseModel):
    """
    Common user fields shared across schemas.
    """

    username: str = Field(
        min_length=3,
        max_length=100,
    )

    email: EmailStr

    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    designation: str | None = Field(
        default=None,
        max_length=100,
    )

    description: str | None = None


# ==========================================================
# Create User
# ==========================================================


class UserCreate(BaseModel):

    username: str = Field(min_length=3, max_length=100)

    email: EmailStr

    password: str = Field(min_length=8, max_length=72)

    first_name: str = Field(min_length=1, max_length=100)

    last_name: str | None = Field(default=None, max_length=100)

    phone: str | None = Field(default=None, max_length=20)

    designation: str | None = Field(default=None, max_length=100)

    organization_id: UUID

    role_id: UUID

    batch_id: UUID | None = None

    description: str | None = None


# ==========================================================
# Update User
# ==========================================================


class UserUpdate(BaseModel):
    """
    Schema used for updating user information.

    API:
        PUT /api/users/{user_id}
    """

    username: str | None = Field(default=None, min_length=3, max_length=100)

    email: EmailStr | None = None

    password: str | None = Field(default=None, min_length=8, max_length=72)

    first_name: str | None = Field(default=None, min_length=1, max_length=100)

    last_name: str | None = Field(default=None, max_length=100)

    phone: str | None = Field(default=None, max_length=20)

    designation: str | None = Field(default=None, max_length=100)

    organization_id: UUID | None = None

    role_id: UUID | None = None

    batch_id: UUID | None = None

    description: str | None = None


# ==========================================================
# Nested Role Response
# ==========================================================


class RoleNestedResponse(BaseModel):
    """
    Nested role details returned with user.
    """

    id: UUID
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


# ==========================================================
# Organization Membership Response
# ==========================================================


class OrganizationMembershipResponse(BaseModel):
    """
    Organization membership details returned with user profile.
    """

    organization_id: UUID
    organization_name: str = ""
    role: RoleNestedResponse | None = None
    batch_id: UUID | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "organization_id") or hasattr(data, "organization"):
            org_id = getattr(data, "organization_id", None)
            org_obj = getattr(data, "organization", None)
            org_name = getattr(org_obj, "name", "") if org_obj else ""
            if not org_name and hasattr(data, "organization_name"):
                org_name = getattr(data, "organization_name", "")
            return {
                "organization_id": org_id,
                "organization_name": org_name,
                "role": getattr(data, "role", None),
                "batch_id": getattr(data, "batch_id", None),
            }
        elif isinstance(data, dict):
            return data
        return data


# ==========================================================
# User Response
# ==========================================================


class UserResponse(BaseModel):
    """
    Complete user response.

    Used for:
        GET /users/{id}
        POST /users
        PUT /users/{id}
    """

    id: UUID

    username: str

    email: EmailStr

    first_name: str

    last_name: str | None = None

    phone: str | None = None

    designation: str | None = None

    description: str | None = None

    is_active: bool = True

    created_at: datetime

    updated_at: datetime

    organization_memberships: list[OrganizationMembershipResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}



# ==========================================================
# User List Item
# ==========================================================


class UserListItem(UserResponse):
    """
    User response item for list operations, matching UserResponse structure.

    Used for:
        GET /api/users/
        GET /api/users/organization/{organization_id}
    """


# ==========================================================
# User List Response
# ==========================================================


class UserListResponse(BaseModel):
    """
    Paginated user list response matching UserResponse format per item.
    """

    data: list[UserResponse]

    page: int

    size: int

    total: int


# ==========================================================
# Current User Profile
# ==========================================================


class UserProfileResponse(UserResponse):
    """
    Logged-in user profile response.

    Used for:
        GET /api/users/me
    """

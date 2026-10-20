from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.organizations.schemas import OrganizationResponse
from app.rbac.schemas import RoleResponse
from app.users.schemas import UserResponse


# ==========================================================
# Create Organization Member
# ==========================================================

class OrganizationMemberCreate(BaseModel):
    """
    Schema for creating an organization member.
    """

    organization_id: UUID
    user_id: UUID
    role_id: UUID


# ==========================================================
# Update Organization Member
# ==========================================================

class OrganizationMemberUpdate(BaseModel):
    """
    Schema for updating an organization member.
    """

    role_id: UUID | None = None
    is_active: bool | None = None


# ==========================================================
# Organization Member Response
# ==========================================================

class OrganizationMemberResponse(BaseModel):
    """
    Complete organization member response with nested relations.
    """

    id: UUID

    organization_id: UUID
    user_id: UUID
    role_id: UUID

    user: UserResponse | None = None
    role: RoleResponse | None = None
    organization: OrganizationResponse | None = None

    joined_at: datetime

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class AssigneeNestedResponse(BaseModel):
    """
    Clean assignee representation for OKR responses without duplicating batch or organization.
    """

    id: UUID

    organization_id: UUID
    user_id: UUID
    role_id: UUID

    user: UserResponse | None = None
    role: RoleResponse | None = None

    joined_at: datetime

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )



# ==========================================================
# Pagination
# ==========================================================

class Pagination(BaseModel):

    page: int
    size: int
    total: int


# ==========================================================
# Organization Member List Response
# ==========================================================

class OrganizationMemberListResponse(BaseModel):
    """
    Paginated response schema for organization member listing.
    """

    data: list[OrganizationMemberResponse]

    pagination: Pagination

    model_config = ConfigDict(
        from_attributes=True
    )
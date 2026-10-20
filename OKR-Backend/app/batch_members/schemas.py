from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.batches.schemas import BatchResponse
from app.rbac.schemas import RoleResponse
from app.users.schemas import UserResponse


# ==========================================================
# Create Batch Member
# ==========================================================

class BatchMemberCreate(BaseModel):
    """
    Schema for creating a batch member.
    """

    batch_id: UUID
    user_id: UUID
    role_id: UUID


# ==========================================================
# Update Batch Member
# ==========================================================

class BatchMemberUpdate(BaseModel):
    """
    Schema for updating a batch member.
    """

    role_id: UUID | None = None
    is_active: bool | None = None


# ==========================================================
# Batch Member Response
# ==========================================================

class BatchMemberResponse(BaseModel):
    """
    Complete batch member response with nested relations.
    """

    id: UUID
    batch_id: UUID
    user_id: UUID
    role_id: UUID

    user: UserResponse | None = None
    role: RoleResponse | None = None
    batch: BatchResponse | None = None

    is_active: bool
    is_deleted: bool

    created_by: UUID | None = None
    updated_by: UUID | None = None
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
# Batch Member List Response
# ==========================================================

class BatchMemberListResponse(BaseModel):
    """
    Paginated response schema for batch member listing.
    """

    data: list[BatchMemberResponse]
    pagination: Pagination

    model_config = ConfigDict(
        from_attributes=True
    )

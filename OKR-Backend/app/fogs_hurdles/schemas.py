from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# =====================================================
# Create FOGS & Hurdles
# =====================================================

class FogsHurdleCreate(BaseModel):
    fogs_hurdles: str
    action_points: str | None = None


# =====================================================
# Update FOGS & Hurdles
# =====================================================

class FogsHurdleUpdate(BaseModel):
    fogs_hurdles: str | None = None
    action_points: str | None = None


# =====================================================
# FOGS & Hurdles Response
# =====================================================

class FogsHurdleResponse(BaseModel):
    id: UUID
    okr_id: UUID
    fogs_hurdles: str
    action_points: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# =====================================================
# Pagination
# =====================================================

class PaginationResponse(BaseModel):
    page: int
    size: int
    total: int


# =====================================================
# FOGS & Hurdles List Response
# =====================================================

class FogsHurdleListResponse(BaseModel):
    data: list[FogsHurdleResponse]
    pagination: PaginationResponse
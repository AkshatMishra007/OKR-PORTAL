from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =====================================================
# Create Weekly Update
# =====================================================

class WeeklyUpdateCreate(BaseModel):

    week_number: int = Field(
        ...,
        ge=1,
    )

    progress: int = Field(
        ...,
        ge=0,

    )

    remarks: str | None = None


# =====================================================
# Update Weekly Update
# =====================================================

class WeeklyUpdateUpdate(BaseModel):

    progress: int | None = Field(
        default=None,
        ge=0,
    )

    remarks: str | None = None


# =====================================================
# Weekly Update Response
# =====================================================

class WeeklyUpdateResponse(BaseModel):

    id: UUID

    okr_id: UUID

    week_number: int

    progress: int

    remarks: str | None

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
# Weekly Update List Response
# =====================================================

class WeeklyUpdateListResponse(BaseModel):

    data: list[WeeklyUpdateResponse]

    pagination: PaginationResponse


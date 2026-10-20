from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =====================================================
# Create Tracker Entry
# =====================================================

class TrackerEntryCreate(BaseModel):

    week_start: date

    opportunities_received: int = Field(
        default=0,
        ge=0,
    )

    opportunities_completed: int = Field(
        default=0,
        ge=0,
    )


# =====================================================
# Update Tracker Entry
# =====================================================

class TrackerEntryUpdate(BaseModel):

    opportunities_received: int | None = Field(
        default=None,
        ge=0,
    )

    opportunities_completed: int | None = Field(
        default=None,
        ge=0,
    )


# =====================================================
# Tracker Entry Response
# =====================================================

class TrackerEntryResponse(BaseModel):

    id: UUID

    okr_id: UUID

    week_start: date

    opportunities_received: int

    opportunities_completed: int

    weekly_completion_efficiency: float | None = None

    target: str | None = None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# =====================================================
# Pagination Response
# =====================================================

class PaginationResponse(BaseModel):

    page: int

    size: int

    total: int


# =====================================================
# Tracker Entry List Response
# =====================================================

class TrackerEntryListResponse(BaseModel):

    data: list[TrackerEntryResponse]

    pagination: PaginationResponse

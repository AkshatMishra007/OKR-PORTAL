from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.batches.models import (
    BatchStatus,
)
from app.batches.models import (
    MeetingDay,
    Quarter,
)


class BatchCreate(BaseModel):

    organization_id: UUID

    name: str

    year: int = Field(
        ...,
        ge=2000,
        le=2100,
    )

    quarter: Quarter

    start_date: date

    end_date: date

    meeting_day: MeetingDay

    batch_users: list[UUID] = Field(default_factory=list)

    batch_admins: list[UUID] = Field(default_factory=list)


class BatchUpdate(BaseModel):

    name: str | None = None

    year: int | None = Field(
        default=None,
        ge=2000,
        le=2100,
    )

    quarter: Quarter | None = None

    start_date: date | None = None

    end_date: date | None = None

    meeting_day: MeetingDay | None = None

    status: BatchStatus | None = None

    batch_users: list[UUID] | None = None

    batch_admins: list[UUID] | None = None


class BatchMemberResponse(BaseModel):

    id: UUID

    name: str

    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class BatchMembersDataResponse(BaseModel):

    users: list[BatchMemberResponse]

    admins: list[BatchMemberResponse]


class BatchMembersResponse(BaseModel):

    data: BatchMembersDataResponse



class BatchResponse(BaseModel):

    id: UUID

    organization_id: UUID

    name: str

    year: int

    quarter: Quarter

    start_date: date

    end_date: date

    meeting_day: MeetingDay

    status: BatchStatus

    is_active: bool

    created_by: UUID | None

    updated_by: UUID | None

    closed_by: UUID | None = None

    closed_at: datetime | None = None

    created_at: datetime

    updated_at: datetime

    users: list[BatchMemberResponse] = []

    admins: list[BatchMemberResponse] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


class BatchDetailResponse(BaseModel):

    data: BatchResponse



class PaginationResponse(BaseModel):

    page: int

    size: int

    total: int


class BatchListResponse(BaseModel):

    data: list[BatchResponse]

    pagination: PaginationResponse
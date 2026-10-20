from datetime import datetime
from uuid import UUID

from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator

from app.batches.schemas import BatchResponse
from app.organization_members.schemas import AssigneeNestedResponse, OrganizationMemberResponse
from app.organizations.schemas import OrganizationResponse
from app.users.schemas import UserResponse


# =========================
# Pagination
# =========================

class PaginationResponse(BaseModel):
    page: int
    size: int
    total: int


# =========================
# Create OKR
# =========================

class OKRCreate(BaseModel):
    batch_id: UUID
    assigned_to: UUID

    objective: str
    target: str | None = None
    key_results: str = ""

    okr_type: str

    tracker_enabled: bool = False


# =========================
# Update OKR
# =========================

class OKRUpdate(BaseModel):
    objective: str | None = None
    target: str | None = None
    key_results: str | None = None

    okr_type: str | None = None

    tracker_enabled: bool | None = None
    status: str | None = None


# =========================
# OKR Response
# =========================

class OKRResponse(BaseModel):
    id: UUID

    batch_id: UUID
    batch: BatchResponse | None = None

    assigned_to: UUID
    assignee: AssigneeNestedResponse | None = None

    organization_id: UUID | None = None
    organization: OrganizationResponse | None = None


    objective: str
    target: str | None = None

    key_results: str

    okr_type: str
    tracker_enabled: bool

    status: str

    total_opportunities_received: int = 0
    total_opportunities_completed: int = 0
    parsed_target: float | None = None
    progress_percentage: float = 0.0
    display_progress_percentage: float = 0.0
    expected_time_progress_percentage: float = 0.0

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

    @model_validator(mode="before")
    def map_assigned_to_user_id(cls, data: Any) -> Any:
        if hasattr(data, "assignee") and data.assignee:
            user_id = getattr(data.assignee, "user_id", None)
            if user_id:
                if isinstance(data, dict):
                    data["assigned_to"] = user_id
                else:
                    try:
                        setattr(data, "assigned_to", user_id)
                    except AttributeError:
                        object.__setattr__(data, "assigned_to", user_id)
        elif isinstance(data, dict) and "assignee" in data:
            assignee = data["assignee"]
            if isinstance(assignee, dict) and "user_id" in assignee:
                data["assigned_to"] = assignee["user_id"]
            elif hasattr(assignee, "user_id"):
                data["assigned_to"] = assignee.user_id
        return data


# =========================
# My OKR List Response
# =========================

class OKRListResponse(BaseModel):
    data: list[OKRResponse]

    pagination: PaginationResponse
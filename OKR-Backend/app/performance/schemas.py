from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PerformanceWeeklyUpdate(BaseModel):
    week_number: int
    progress: int
    remarks: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PerformanceTrackerEntry(BaseModel):
    week_start: date
    opportunities_received: int
    opportunities_completed: int

    model_config = ConfigDict(from_attributes=True)


class PerformanceOKR(BaseModel):
    id: UUID
    objective: str
    target: str | None = None
    key_results: str
    okr_type: str
    status: str

    batch_id: UUID
    assigned_to: UUID
    assigned_to_name: str | None = None

    progress_percentage: float = 0.0
    display_progress_percentage: float = 0.0
    expected_time_progress_percentage: float = 0.0

    total_opportunities_received: int = 0
    total_opportunities_completed: int = 0

    weekly_updates: list[PerformanceWeeklyUpdate] = Field(
        default_factory=list
    )
    tracker_entries: list[PerformanceTrackerEntry] = Field(
        default_factory=list
    )

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PerformanceWeeklyScore(BaseModel):
    week_number: int
    score: float


class PerformanceUser(BaseModel):
    user_id: UUID
    user_name: str
    score: float
    award: str
    weekly_scores: list[PerformanceWeeklyScore] = Field(
        default_factory=list
    )


class PerformanceAwardDistribution(BaseModel):
    GLADIATOR: int = 0
    PLATINUM: int = 0
    GOLD: int = 0
    BRONZE: int = 0


class PerformanceMetrics(BaseModel):
    top_score: float = 0.0
    lowest_score: float = 0.0
    average_score: float = 0.0
    gladiator_count: int = 0
    award_distribution: PerformanceAwardDistribution = Field(
        default_factory=PerformanceAwardDistribution
    )


class PerformanceResponse(BaseModel):
    data: list[PerformanceOKR] = Field(default_factory=list)
    users: list[PerformanceUser] = Field(default_factory=list)
    metrics: PerformanceMetrics = Field(
        default_factory=PerformanceMetrics
    )
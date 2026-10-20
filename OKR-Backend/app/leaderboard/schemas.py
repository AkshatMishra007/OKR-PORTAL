from uuid import UUID

from pydantic import BaseModel, Field


class LeaderboardItem(BaseModel):
    rank: int
    user_id: UUID
    name: str
    team: str
    score: float = Field(ge=0, le=100)
    award: str


class MyRankResponse(BaseModel):
    rank: int | None = None
    score: float | None = None
    award: str | None = None


class AwardDistribution(BaseModel):
    gladiator: int = 0
    platinum: int = 0
    gold: int = 0
    bronze: int = 0


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardItem]
    my_rank: MyRankResponse
    award_distribution: AwardDistribution
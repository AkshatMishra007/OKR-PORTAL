from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.leaderboard.repository import (
    get_organization_members,
    get_organization_okrs,
    get_user_organization,
)
from app.leaderboard.schemas import (
    AwardDistribution,
    LeaderboardItem,
    LeaderboardResponse,
    MyRankResponse,
)
from app.my_okr.service import _enrich_okrs_bulk


def get_award(score: float) -> str:
    """Determine the award tier from a 0–100 leaderboard score."""
    if score >= 90:
        return "Gladiator"
    if score >= 80:
        return "Platinum"
    if score >= 60:
        return "Gold"
    return "Bronze"


def _get_okr_overall_progress(okr) -> float:
    """
    Get overall progress for one OKR.
    Tracker-enabled OKRs use tracker-derived progress.
    Tracker-disabled OKRs use the latest saved weekly-update
    progress, when available.
    """
    if getattr(okr, "tracker_enabled", False):
        raw_progress = getattr(okr, "display_progress_percentage", 0.0)
    else:
        weekly_updates = [
            update
            for update in (getattr(okr, "weekly_updates", []) or [])
            if not getattr(update, "is_deleted", False)
        ]

        def _update_sort_key(update):
            ts = getattr(update, "updated_at", None) or getattr(update, "created_at", None)
            if ts is not None and hasattr(ts, "timestamp"):
                try:
                    return ts.timestamp()
                except Exception:
                    pass
            return float(getattr(update, "week_number", 0) or 0)

        latest_update = max(
            weekly_updates,
            key=_update_sort_key,
            default=None,
        )
        raw_progress = (
            getattr(latest_update, "progress", 0.0)
            if latest_update is not None
            else 0.0
        )
    try:
        return max(0.0, min(100.0, float(raw_progress or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def get_leaderboard_service(
    db: Session,
    current_user_id: UUID,
) -> LeaderboardResponse:
    """Build one organization-wide leaderboard using Team OKR progress."""
    membership = get_user_organization(db=db, user_id=current_user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active organization membership not found.",
        )

    organization_id = membership.organization_id
    members = get_organization_members(db=db, organization_id=organization_id)
    okrs = get_organization_okrs(db=db, organization_id=organization_id)

    # Enrich tracker-enabled OKRs using the shared My OKR calculation.
    _enrich_okrs_bulk(db=db, okrs=okrs)

    # Initialize every active organization member, including those without OKRs.
    user_scores: dict[UUID, list[float]] = defaultdict(list)
    user_details: dict[UUID, dict[str, str]] = {}

    for member in members:
        user = member.user
        if not user or getattr(user, "is_deleted", False):
            continue
        user_scores[user.id]  # initialize with no OKRs -> score 0
        name = " ".join(
            part
            for part in (
                getattr(user, "first_name", None),
                getattr(user, "last_name", None),
            )
            if part
        ).strip() or getattr(user, "name", None) or "Unknown User"

        user_details[user.id] = {
            "name": name,
            "team": getattr(member, "organization_name", None) or "",
        }

    # Calculate each user's score from the overall progress of their OKRs.
    for okr in okrs:
        member = okr.assignee
        user = member.user if member else None
        if not user or user.id not in user_details:
            continue
        user_scores[user.id].append(_get_okr_overall_progress(okr))

    leaderboard_data = []
    for user_id, scores in user_scores.items():
        average_score = sum(scores) / len(scores) if scores else 0.0
        average_score = round(max(0.0, min(100.0, average_score)), 2)
        leaderboard_data.append(
            {
                "user_id": user_id,
                "name": user_details[user_id]["name"],
                "team": user_details[user_id]["team"],
                "score": average_score,
                "award": get_award(average_score),
            }
        )

    # Deterministic ordering: score descending, then case-insensitive name, then ID.
    leaderboard_data.sort(
        key=lambda item: (
            -item["score"],
            item["name"].casefold(),
            str(item["user_id"]),
        )
    )

    items = [
        LeaderboardItem(
            rank=index,
            user_id=item["user_id"],
            name=item["name"],
            team=item["team"],
            score=item["score"],
            award=item["award"],
        )
        for index, item in enumerate(leaderboard_data, start=1)
    ]

    my_rank = MyRankResponse()
    for item in items:
        if item.user_id == current_user_id:
            my_rank = MyRankResponse(
                rank=item.rank,
                score=item.score,
                award=item.award,
            )
            break

    distribution = AwardDistribution()
    for item in items:
        if item.award == "Gladiator":
            distribution.gladiator += 1
        elif item.award == "Platinum":
            distribution.platinum += 1
        elif item.award == "Gold":
            distribution.gold += 1
        else:
            distribution.bronze += 1

    return LeaderboardResponse(
        items=items,
        my_rank=my_rank,
        award_distribution=distribution,
    )

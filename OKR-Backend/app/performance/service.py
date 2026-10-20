from collections import defaultdict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.my_okr.service import _enrich_okrs_bulk
from app.performance import repository


def _get_user_name(okr) -> str:
    """
    Resolve a display name from the eagerly loaded OKR assignee.
    """
    assignee = getattr(okr, "assignee", None)

    if not assignee:
        return "Unknown User"

    user = getattr(assignee, "user", None)

    if not user:
        return "Unknown User"

    full_name = getattr(user, "full_name", None)

    if full_name:
        return full_name

    first_name = getattr(user, "first_name", None) or ""
    last_name = getattr(user, "last_name", None) or ""

    name = f"{first_name} {last_name}".strip()

    if name:
        return name

    email = getattr(user, "email", None)

    return email or "Unknown User"


def _calculate_award(score: float) -> str:
    """
    Convert a 0-100 performance score into the portal award band.
    """
    if score >= 90:
        return "GLADIATOR"

    if score >= 80:
        return "PLATINUM"

    if score >= 60:
        return "GOLD"

    return "BRONZE"


def _calculate_user_scores(okrs):
    """
    Calculate user-level performance from enriched OKRs.

    User score = average of display_progress_percentage
    across the user's active OKRs.
    """
    from app.performance.schemas import (
        PerformanceUser,
        PerformanceWeeklyScore,
    )

    user_okrs = defaultdict(list)

    for okr in okrs:
        user_id = getattr(okr, "assigned_to", None)

        if user_id:
            user_okrs[user_id].append(okr)

    users = []

    for user_id, user_okr_list in user_okrs.items():
        scores = []

        for okr in user_okr_list:
            score = float(
                getattr(
                    okr,
                    "display_progress_percentage",
                    0.0,
                )
                or 0.0
            )

            scores.append(max(0.0, min(score, 100.0)))

        user_score = (
            round(sum(scores) / len(scores), 2)
            if scores
            else 0.0
        )

        weekly_values = defaultdict(list)

        for okr in user_okr_list:
            for update in getattr(
                okr,
                "weekly_updates",
                [],
            ):
                week_number = getattr(
                    update,
                    "week_number",
                    None,
                )

                progress = getattr(
                    update,
                    "progress",
                    0,
                )

                if week_number is None:
                    continue

                try:
                    progress = float(progress)
                except (TypeError, ValueError):
                    progress = 0.0

                progress = max(
                    0.0,
                    min(progress, 100.0),
                )

                weekly_values[int(week_number)].append(
                    progress
                )

        weekly_scores = []

        max_week = (
            max(weekly_values.keys())
            if weekly_values
            else 0
        )

        for week_number in range(1, max_week + 1):
            values = weekly_values.get(
                week_number,
                [],
            )

            if values:
                weekly_score = round(
                    sum(values) / len(values),
                    2,
                )
            else:
                weekly_score = 0.0

            weekly_scores.append(
                PerformanceWeeklyScore(
                    week_number=week_number,
                    score=weekly_score,
                )
            )

        user_name = _get_user_name(
            user_okr_list[0]
        )

        users.append(
            PerformanceUser(
                user_id=user_id,
                user_name=user_name,
                score=user_score,
                award=_calculate_award(user_score),
                weekly_scores=weekly_scores,
            )
        )

    return users


def _calculate_metrics(users):
    from app.performance.schemas import (
        PerformanceAwardDistribution,
        PerformanceMetrics,
    )

    if not users:
        return PerformanceMetrics(
            top_score=0.0,
            lowest_score=0.0,
            average_score=0.0,
            gladiator_count=0,
            award_distribution=PerformanceAwardDistribution(),
        )

    scores = [
        float(user.score)
        for user in users
    ]

    distribution = PerformanceAwardDistribution()

    for user in users:
        if user.award == "GLADIATOR":
            distribution.GLADIATOR += 1

        elif user.award == "PLATINUM":
            distribution.PLATINUM += 1

        elif user.award == "GOLD":
            distribution.GOLD += 1

        else:
            distribution.BRONZE += 1

    return PerformanceMetrics(
        top_score=float(max(scores)),
        lowest_score=float(min(scores)),
        average_score=float(sum(scores) / len(scores)),
        gladiator_count=distribution.GLADIATOR,
        award_distribution=distribution,
    )


def get_performance(
    db: Session,
    current_user_id: UUID,
    batch_id: UUID | None = None,
):
    """
    Get performance data and calculated performance metrics
    for the current user's organization.

    Task 469 adds user-level score calculation, award
    classification, weekly scores and aggregate metrics.
    """

    membership = repository.get_active_organization_membership(
        db=db,
        user_id=current_user_id,
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active organization membership not found.",
        )

    organization_id = membership.organization_id

    if batch_id is not None:
        batch = repository.get_batch_for_organization(
            db=db,
            batch_id=batch_id,
            organization_id=organization_id,
        )

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found in your organization.",
            )

    okrs = repository.get_performance_okrs(
        db=db,
        organization_id=organization_id,
        batch_id=batch_id,
    )

    # Reuse the existing OKR progress calculation.
    enriched_okrs = _enrich_okrs_bulk(
        db=db,
        okrs=okrs,
    )

    users = _calculate_user_scores(
        enriched_okrs
    )

    metrics = _calculate_metrics(users)

    # Add display names to the existing OKR response.
    for okr in enriched_okrs:
        assigned_to = getattr(
            okr,
            "assigned_to",
            None,
        )

        matching_user = next(
            (
                user
                for user in users
                if user.user_id == assigned_to
            ),
            None,
        )

        if matching_user:
            if isinstance(okr, dict):
                okr["assigned_to_name"] = (
                    matching_user.user_name
                )
            else:
                try:
                    setattr(
                        okr,
                        "assigned_to_name",
                        matching_user.user_name,
                    )
                except Exception:
                    pass

    return {
        "data": enriched_okrs,
        "users": [user.model_dump() for user in users],
        "metrics": metrics.model_dump(),
    }
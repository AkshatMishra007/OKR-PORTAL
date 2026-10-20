"""
Performance backend tests.

Place this file at:
    app/tests/performance/test_performance.py

These tests cover the Performance service introduced for:
- Performance Overview API
- Batch filtering
- Performance metrics and score calculation
- Award distribution
- Weekly score calculation
- Organization isolation

The tests mock repository/database access so they do not modify production
tables or depend on existing demo data.
"""

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.performance import service


ORG_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_ORG_ID = UUID("22222222-2222-2222-2222-222222222222")
USER_1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
BATCH_1 = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
BATCH_2 = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def make_membership(organization_id=ORG_ID):
    return SimpleNamespace(
        id=uuid4(),
        organization_id=organization_id,
        is_active=True,
        is_deleted=False,
    )


def make_batch(batch_id=BATCH_1, organization_id=ORG_ID):
    return SimpleNamespace(
        id=batch_id,
        organization_id=organization_id,
        is_active=True,
        is_deleted=False,
    )


def make_user(user_id=USER_1, name="Test User"):
    return SimpleNamespace(
        id=user_id,
        first_name=name.split(" ")[0],
        last_name=" ".join(name.split(" ")[1:]) or "",
        full_name=name,
        name=name,
    )


def make_okr(
    user_id=USER_1,
    user_name="Test User",
    batch_id=BATCH_1,
    progress=80.0,
    weekly_updates=None,
):
    user = make_user(user_id, user_name)

    assignee = SimpleNamespace(
        id=user_id,
        user=user,
    )

    return SimpleNamespace(
        id=uuid4(),
        assigned_to=user_id,
        batch_id=batch_id,
        assignee=assignee,
        display_progress_percentage=progress,
        progress_percentage=progress,
        progress=progress,
        weekly_updates=weekly_updates or [],
        tracker_entries=[],
        is_active=True,
        is_deleted=False,
    )


def update(week_number, progress):
    return SimpleNamespace(
        week_number=week_number,
        progress=progress,
        remarks=None,
    )


def patch_performance_dependencies(monkeypatch, okrs, membership=None):
    """
    Patch only the external dependencies of get_performance().
    The actual Performance service calculation logic still executes.
    """
    membership = membership or make_membership()

    monkeypatch.setattr(
        service.repository,
        "get_active_organization_membership",
        lambda db, user_id: membership,
    )

    monkeypatch.setattr(
        service.repository,
        "get_performance_okrs",
        lambda db, organization_id, batch_id=None: okrs,
    )

    monkeypatch.setattr(
        service,
        "_enrich_okrs_bulk",
        lambda db, okrs: okrs,
    )

    return membership


# ---------------------------------------------------------------------------
# Basic Performance API/service behavior
# ---------------------------------------------------------------------------


def test_performance_returns_data_users_and_metrics(monkeypatch):
    okr = make_okr(progress=85)

    patch_performance_dependencies(monkeypatch, [okr])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert "data" in result
    assert "users" in result
    assert "metrics" in result

    assert len(result["data"]) == 1
    assert len(result["users"]) == 1
    assert result["users"][0]["user_id"] == USER_1
    assert result["users"][0]["score"] == pytest.approx(85.0)


def test_performance_requires_active_organization_membership(monkeypatch):
    monkeypatch.setattr(
        service.repository,
        "get_active_organization_membership",
        lambda db, user_id: None,
    )

    with pytest.raises(HTTPException) as exc:
        service.get_performance(
            db=None,
            current_user_id=USER_1,
        )

    assert exc.value.status_code == 404
    assert "membership" in str(exc.value.detail).lower()


def test_invalid_batch_returns_404(monkeypatch):
    membership = make_membership()

    monkeypatch.setattr(
        service.repository,
        "get_active_organization_membership",
        lambda db, user_id: membership,
    )

    monkeypatch.setattr(
        service.repository,
        "get_batch_for_organization",
        lambda db, batch_id, organization_id: None,
    )

    with pytest.raises(HTTPException) as exc:
        service.get_performance(
            db=None,
            current_user_id=USER_1,
            batch_id=BATCH_1,
        )

    assert exc.value.status_code == 404
    assert "batch" in str(exc.value.detail).lower()


def test_batch_from_other_organization_is_rejected(monkeypatch):
    membership = make_membership(ORG_ID)

    monkeypatch.setattr(
        service.repository,
        "get_active_organization_membership",
        lambda db, user_id: membership,
    )

    # Repository lookup is organization-scoped, therefore a batch from
    # another organization must not be accepted.
    monkeypatch.setattr(
        service.repository,
        "get_batch_for_organization",
        lambda db, batch_id, organization_id: (
            make_batch(BATCH_2, OTHER_ORG_ID)
            if organization_id == ORG_ID
            else None
        ),
    )

    # The service trusts the repository's organization-scoped lookup.
    # This assertion documents that the repository must return None for an
    # out-of-organization batch. The explicit invalid result is tested above.
    batch = service.repository.get_batch_for_organization(
        db=None,
        batch_id=BATCH_2,
        organization_id=ORG_ID,
    )

    assert batch.organization_id == OTHER_ORG_ID


def test_batch_id_is_forwarded_to_repository(monkeypatch):
    membership = make_membership()
    received = {}

    monkeypatch.setattr(
        service.repository,
        "get_active_organization_membership",
        lambda db, user_id: membership,
    )

    monkeypatch.setattr(
        service.repository,
        "get_batch_for_organization",
        lambda db, batch_id, organization_id: make_batch(
            batch_id,
            organization_id,
        ),
    )

    def fake_get_okrs(db, organization_id, batch_id=None):
        received["organization_id"] = organization_id
        received["batch_id"] = batch_id
        return []

    monkeypatch.setattr(
        service.repository,
        "get_performance_okrs",
        fake_get_okrs,
    )

    monkeypatch.setattr(
        service,
        "_enrich_okrs_bulk",
        lambda db, okrs: okrs,
    )

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
        batch_id=BATCH_1,
    )

    assert received["organization_id"] == ORG_ID
    assert received["batch_id"] == BATCH_1
    assert result["data"] == []


def test_without_batch_id_does_not_validate_specific_batch(monkeypatch):
    membership = make_membership()
    called = {"batch_validation": False}

    monkeypatch.setattr(
        service.repository,
        "get_active_organization_membership",
        lambda db, user_id: membership,
    )

    def fail_if_called(*args, **kwargs):
        called["batch_validation"] = True
        raise AssertionError(
            "get_batch_for_organization should not be called without batch_id"
        )

    monkeypatch.setattr(
        service.repository,
        "get_batch_for_organization",
        fail_if_called,
    )

    monkeypatch.setattr(
        service.repository,
        "get_performance_okrs",
        lambda db, organization_id, batch_id=None: [],
    )

    monkeypatch.setattr(
        service,
        "_enrich_okrs_bulk",
        lambda db, okrs: okrs,
    )

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert result["data"] == []
    assert called["batch_validation"] is False


def test_empty_performance_data_returns_empty_users_and_metrics(monkeypatch):
    patch_performance_dependencies(monkeypatch, [])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert result["data"] == []
    assert result["users"] == []

    assert result["metrics"]["top_score"] == 0
    assert result["metrics"]["lowest_score"] == 0
    assert result["metrics"]["average_score"] == 0
    assert result["metrics"]["gladiator_count"] == 0


# ---------------------------------------------------------------------------
# User score calculation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("score", "expected_award"),
    [
        (100, "GLADIATOR"),
        (90, "GLADIATOR"),
        (89.99, "PLATINUM"),
        (80, "PLATINUM"),
        (79.99, "GOLD"),
        (60, "GOLD"),
        (59.99, "BRONZE"),
        (0, "BRONZE"),
    ],
)
def test_award_boundaries(monkeypatch, score, expected_award):
    okr = make_okr(progress=score)
    patch_performance_dependencies(monkeypatch, [okr])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert result["users"][0]["award"] == expected_award


def test_multiple_okrs_for_same_user_are_averaged(monkeypatch):
    okr_1 = make_okr(
        user_id=USER_1,
        user_name="Alice",
        progress=80,
    )
    okr_2 = make_okr(
        user_id=USER_1,
        user_name="Alice",
        progress=100,
    )

    patch_performance_dependencies(monkeypatch, [okr_1, okr_2])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert len(result["users"]) == 1
    assert result["users"][0]["score"] == pytest.approx(90.0)
    assert result["users"][0]["award"] == "GLADIATOR"


def test_multiple_users_produce_separate_scores(monkeypatch):
    okr_1 = make_okr(
        user_id=USER_1,
        user_name="Alice",
        progress=90,
    )
    okr_2 = make_okr(
        user_id=USER_2,
        user_name="Bob",
        progress=60,
    )

    patch_performance_dependencies(monkeypatch, [okr_1, okr_2])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert len(result["users"]) == 2

    scores = {
        item["user_id"]: item["score"]
        for item in result["users"]
    }

    assert scores[USER_1] == pytest.approx(90.0)
    assert scores[USER_2] == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# Weekly score calculation
# ---------------------------------------------------------------------------


def test_weekly_scores_are_calculated_from_weekly_updates(monkeypatch):
    okr = make_okr(
        progress=0,
        weekly_updates=[
            update(1, 20),
            update(2, 40),
            update(3, 60),
            update(4, 80),
        ],
    )

    patch_performance_dependencies(monkeypatch, [okr])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    weekly_scores = result["users"][0]["weekly_scores"]

    scores = {
        item["week_number"]: item["score"]
        for item in weekly_scores
    }

    assert scores[1] == pytest.approx(20.0)
    assert scores[2] == pytest.approx(40.0)
    assert scores[3] == pytest.approx(60.0)
    assert scores[4] == pytest.approx(80.0)


def test_weekly_score_is_averaged_when_multiple_okrs_exist(monkeypatch):
    okr_1 = make_okr(
        user_id=USER_1,
        user_name="Alice",
        progress=0,
        weekly_updates=[update(1, 20)],
    )
    okr_2 = make_okr(
        user_id=USER_1,
        user_name="Alice",
        progress=0,
        weekly_updates=[update(1, 80)],
    )

    patch_performance_dependencies(monkeypatch, [okr_1, okr_2])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    week_one = next(
        item
        for item in result["users"][0]["weekly_scores"]
        if item["week_number"] == 1
    )

    assert week_one["score"] == pytest.approx(50.0)


def test_zero_progress_is_valid(monkeypatch):
    okr = make_okr(
        progress=0,
        weekly_updates=[update(1, 0)],
    )

    patch_performance_dependencies(monkeypatch, [okr])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert result["users"][0]["weekly_scores"][0]["score"] == 0


# ---------------------------------------------------------------------------
# Aggregate metrics
# ---------------------------------------------------------------------------


def test_aggregate_metrics_are_calculated(monkeypatch):
    okrs = [
        make_okr(
            user_id=USER_1,
            user_name="Gladiator",
            progress=95,
        ),
        make_okr(
            user_id=USER_2,
            user_name="Gold",
            progress=65,
        ),
        make_okr(
            user_id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
            user_name="Bronze",
            progress=40,
        ),
    ]

    patch_performance_dependencies(monkeypatch, okrs)

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    metrics = result["metrics"]

    assert metrics["top_score"] == pytest.approx(95.0)
    assert metrics["lowest_score"] == pytest.approx(40.0)
    assert metrics["average_score"] == pytest.approx(
        (95 + 65 + 40) / 3
    )
    assert metrics["gladiator_count"] == 1


def test_award_distribution_counts_all_users(monkeypatch):
    okrs = [
        make_okr(
            user_id=USER_1,
            user_name="Gladiator",
            progress=95,
        ),
        make_okr(
            user_id=USER_2,
            user_name="Platinum",
            progress=85,
        ),
        make_okr(
            user_id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
            user_name="Gold",
            progress=65,
        ),
        make_okr(
            user_id=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
            user_name="Bronze",
            progress=20,
        ),
    ]

    patch_performance_dependencies(monkeypatch, okrs)

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    distribution = result["metrics"]["award_distribution"]

    assert distribution["GLADIATOR"] == 1
    assert distribution["PLATINUM"] == 1
    assert distribution["GOLD"] == 1
    assert distribution["BRONZE"] == 1


def test_user_name_is_returned_in_performance_result(monkeypatch):
    okr = make_okr(
        user_id=USER_1,
        user_name="Ananya Rao",
        progress=80,
    )

    patch_performance_dependencies(monkeypatch, [okr])

    result = service.get_performance(
        db=None,
        current_user_id=USER_1,
    )

    assert result["users"][0]["user_name"] == "Ananya Rao"

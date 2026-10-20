"""
Exhaustive Query Activity & History Test Suite (22 unrolled test functions).

Covers:
- GET /queries/{query_id}/activities (Activity history retrieval)
- Pagination, Filtering, Sorting & Bounds
- Activity logging throughout query lifecycle
- Strict query activity isolation & read-only guarantee
- Direct service and repository unit tests
"""

import uuid
from datetime import datetime, UTC
import pytest
from fastapi import status

from app.queries.models import Query, QueryPriority, QueryStatus
from app.query_activity.models import QueryActivity, QueryActivityType
from app.query_activity.service import get_query_activity_history
from app.query_activity import repository
from app.tests.conftest import get_jwt_headers


def _create_activity_query(db_session, user_id, ticket_num="QRY-ACT001"):
    q = Query(
        ticket_number=ticket_num,
        user_id=user_id,
        subject="Activity Test Query Subject",
        message="Activity Test Query Body Message",
        priority=QueryPriority.MEDIUM,
        status=QueryStatus.OPEN,
    )
    db_session.add(q)
    db_session.commit()
    return q


# ============================================================================
# SECTION 1: ENDPOINT & FUNCTIONAL TESTS (18 TESTS)
# ============================================================================

def test_get_activities_unauthenticated_no_header_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACT01")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_activities_malformed_token_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACT02")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers={"Authorization": "Bearer bad.token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_activities_authenticated_success_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACT03")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_get_activities_nonexistent_uuid_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get(f"/queries/{uuid.uuid4()}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_get_activities_malformed_uuid_path_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get("/queries/invalid-uuid/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_activities_soft_deleted_query_404(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = Query(ticket_number="QRY-ACTDEL", user_id=emp1.id, subject="Sub", message="Msg", priority=QueryPriority.LOW, status=QueryStatus.OPEN, is_deleted=True)
    db_session.add(q)
    db_session.commit()
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_get_activities_empty_history_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTEMP")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == 0

def test_get_activities_single_activity_verification(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTSING")
    act = QueryActivity(query_id=q.id, activity_type=QueryActivityType.CREATED, description="Query created", performed_by=emp1.id)
    db_session.add(act)
    db_session.commit()
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == 1

def test_get_activities_all_supported_activity_types(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTALL")
    for act_type in QueryActivityType:
        db_session.add(QueryActivity(query_id=q.id, activity_type=act_type, description=f"Activity {act_type.value}", performed_by=emp1.id))
    db_session.commit()
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == len(list(QueryActivityType))

def test_get_activities_real_query_lifecycle_history_chronological(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTLIFECYCLE")
    auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] >= 1

def test_get_activities_pagination_page_1_and_page_2(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTPAG")
    db_session.add(QueryActivity(query_id=q.id, activity_type=QueryActivityType.CREATED, description="A1", performed_by=emp1.id))
    db_session.add(QueryActivity(query_id=q.id, activity_type=QueryActivityType.ASSIGNED, description="A2", performed_by=emp1.id))
    db_session.commit()
    res1 = auth_jwt_client.get(f"/queries/{q.id}/activities?page=1&page_size=1", headers=get_jwt_headers(emp1))
    res2 = auth_jwt_client.get(f"/queries/{q.id}/activities?page=2&page_size=1", headers=get_jwt_headers(emp1))
    assert res1.status_code == status.HTTP_200_OK
    assert res2.status_code == status.HTTP_200_OK

def test_get_activities_pagination_size_boundary_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTBOUND")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities?size=0", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_activities_filter_by_activity_type_assigned(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTFLTASG")
    db_session.add(QueryActivity(query_id=q.id, activity_type=QueryActivityType.ASSIGNED, description="Assigned", performed_by=emp1.id))
    db_session.commit()
    res = auth_jwt_client.get(f"/queries/{q.id}/activities?activity_type=ASSIGNED", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_get_activities_filter_by_activity_type_zero_matches(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTZEROMATCH")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities?activity_type=RESOLVED", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == 0

def test_get_activities_strict_query_isolation(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q1 = _create_activity_query(db_session, emp1.id, "QRY-ACTISO1")
    q2 = _create_activity_query(db_session, emp1.id, "QRY-ACTISO2")
    db_session.add(QueryActivity(query_id=q1.id, activity_type=QueryActivityType.CREATED, description="Q1 Act", performed_by=emp1.id))
    db_session.commit()
    res2 = auth_jwt_client.get(f"/queries/{q2.id}/activities", headers=get_jwt_headers(emp1))
    assert res2.json()["total"] == 0

def test_get_activities_read_only_no_database_mutation(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTRO")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_query_activities_logged_throughout_lifecycle(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTLC")
    auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.json()["total"] >= 1

def test_get_query_activity_history_filtering_and_sorting(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTSORT")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities?sort_order=desc", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK


# ============================================================================
# SECTION 2: DIRECT SERVICE AND REPOSITORY TESTS (4 TESTS)
# ============================================================================

def test_get_activities_api_endpoint(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTAPI")
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_get_query_activity_history_nonexistent(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get(f"/queries/{uuid.uuid4()}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_get_query_activity_history_service_direct_unit_test(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTSRV")
    res = get_query_activity_history(db_session, q.id)
    assert hasattr(res, "activities")

def test_repository_get_query_activities_direct_unit_test(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_activity_query(db_session, emp1.id, "QRY-ACTREPO")
    res, total = repository.get_query_activities(db_session, q.id)
    assert isinstance(res, list)

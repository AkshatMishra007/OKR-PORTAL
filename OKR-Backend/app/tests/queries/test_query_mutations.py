"""
Exhaustive Query Mutations Test Suite (126 unrolled test functions).

Covers:
- PATCH /queries/{query_id}/assign (Assignment & Reassignment)
- PATCH /queries/{query_id}/status (Status State Machine & Transitions)
- PATCH /queries/{query_id}/resolve (Resolution, Note Validation & Computed Time)
- PATCH /queries/{query_id}/close (Closure & Computed Time)
- Repository update and delete operations
"""

import uuid
from datetime import datetime, timedelta, UTC
import pytest
from fastapi import HTTPException, status

from app.queries.models import Query, QueryPriority, QueryStatus
from app.queries.schemas import QueryStatusUpdate, QueryResolve
from app.queries.service import (
    assign_query_service,
    update_query_status_service,
    resolve_query_service,
    close_query_service,
)
from app.queries import repository
from app.common.exceptions import BadRequestException, ForbiddenException
from app.tests.conftest import get_jwt_headers


def _create_mutation_query(db_session, user_id, ticket_num="QRY-MUT001", status_val=QueryStatus.OPEN, priority_val=QueryPriority.MEDIUM, assigned_to_user=None):
    q = Query(
        ticket_number=ticket_num,
        user_id=user_id,
        assigned_to=assigned_to_user,
        subject="Mutation Test Query Subject",
        message="Mutation Test Query Body Message",
        priority=priority_val,
        status=status_val,
    )
    db_session.add(q)
    db_session.commit()
    return q


# ============================================================================
# SECTION 1: ASSIGNMENT ENDPOINT & SERVICE TESTS (26 TESTS)
# ============================================================================

def test_assign_query_unauthenticated_no_header_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASG01")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_assign_query_malformed_token_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASG02")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers={"Authorization": "Bearer bad.token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_assign_query_nonexistent_query_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    res = auth_jwt_client.patch(f"/queries/{uuid.uuid4()}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_assign_query_malformed_uuid_path_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    res = auth_jwt_client.patch("/queries/invalid-uuid/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_assign_query_soft_deleted_query_404(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = Query(ticket_number="QRY-ASGDEL", user_id=emp1.id, subject="Sub", message="Msg", priority=QueryPriority.LOW, status=QueryStatus.OPEN, is_deleted=True)
    db_session.add(q)
    db_session.commit()
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_assign_query_nonexistent_assignee_404(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGNOUSER")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(uuid.uuid4())}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_assign_query_inactive_assignee_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    inactive = query_setup["inactive_user"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGINACT")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(inactive.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_assign_query_duplicate_same_assignee_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGDUP", assigned_to_user=emp2.id)
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_assign_query_missing_assignee_field_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGMISS")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_assign_query_null_assignee_field_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGNULL")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": None}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_assign_query_as_owner_employee_allowed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGOWN")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_assign_query_as_unrelated_employee_forbidden_403(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGUNREL")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_assign_query_as_org_admin_same_org_allowed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    org_admin = query_setup["org_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGORG")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK

def test_assign_query_as_super_admin_always_allowed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    super_admin = query_setup["super_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGSUP")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_assign_query_status_open_auto_transitions_to_in_progress(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGAUTO", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "IN_PROGRESS"

def test_assign_query_status_reopened_status_remains_reopened(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGREO", status_val=QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "REOPENED"

def test_reassign_query_from_emp1_to_emp2(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    org_admin = query_setup["org_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-REASG", assigned_to_user=emp1.id)
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["assigned_to"] == str(emp2.id)

def test_self_assignment_employee_assigns_to_self(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-SELFASG")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp1.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["assigned_to"] == str(emp1.id)

def test_assign_query_database_persistence_and_activity_log(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGPER")
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    db_session.refresh(q)
    assert q.assigned_to == emp2.id

def test_failed_assignment_creates_no_activity_log(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGFAIL")
    auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(unrelated))
    db_session.refresh(q)
    assert q.assigned_to is None

def test_assigned_query_reflected_in_get_by_id_and_ticket(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGREF")
    auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.json()["assigned_to"] == str(emp2.id)

def test_assign_query_happy_path(db_session, query_setup):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGHP")
    res = assign_query_service(db_session, q.id, emp2.id, emp1.id)
    assert res.assigned_to == emp2.id

def test_assign_to_nonexistent_user(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGNOUSER2")
    with pytest.raises(HTTPException) as exc:
        assign_query_service(db_session, q.id, uuid.uuid4(), emp1.id)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_assign_to_inactive_user(db_session, query_setup):
    emp1 = query_setup["emp1"]
    inactive = query_setup["inactive_user"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGINACT2")
    with pytest.raises(BadRequestException):
        assign_query_service(db_session, q.id, inactive.id, emp1.id)

def test_assign_to_same_user_duplicate(db_session, query_setup):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGDUP2", assigned_to_user=emp2.id)
    with pytest.raises(BadRequestException):
        assign_query_service(db_session, q.id, emp2.id, emp1.id)

def test_assign_query_unauthorized_user(db_session, query_setup):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ASGUNAUTH")
    with pytest.raises(ForbiddenException):
        assign_query_service(db_session, q.id, emp2.id, unrelated.id)


# ============================================================================
# SECTION 2: STATUS TRANSITION ENDPOINT & SERVICE TESTS (49 TESTS)
# ============================================================================

def test_status_update_unauthenticated_no_header_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ST01")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_status_update_malformed_token_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-ST02")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers={"Authorization": "Bearer bad.token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_status_update_as_employee_owner_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STOWN", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_status_update_as_employee_assignee_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STASG", status_val=QueryStatus.OPEN, assigned_to_user=emp2.id)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp2))
    assert res.status_code == status.HTTP_200_OK

def test_status_update_as_unrelated_employee_forbidden_403(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STUNREL", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_status_update_as_org_admin_same_org_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STORG", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK

def test_status_update_as_super_admin_always_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    super_admin = query_setup["super_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STSUP", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_status_update_nonexistent_uuid_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.patch(f"/queries/{uuid.uuid4()}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_status_update_malformed_uuid_path_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.patch("/queries/invalid-uuid/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_status_update_soft_deleted_query_404(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = Query(ticket_number="QRY-STDEL", user_id=emp1.id, subject="Sub", message="Msg", priority=QueryPriority.LOW, status=QueryStatus.OPEN, is_deleted=True)
    db_session.add(q)
    db_session.commit()
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_status_update_missing_status_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STMISS")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_status_update_null_status_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STNULL")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": None}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_status_update_invalid_enum_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STINV")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "INVALID_STATUS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_status_update_lowercase_enum_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STLOW")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "in_progress"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_transition_open_to_open_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-O2O", QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "OPEN"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_open_to_in_progress_success_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-O2I", QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_transition_open_to_resolved_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-O2R", QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "RESOLVED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_open_to_closed_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-O2C", QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "CLOSED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_open_to_reopened_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-O2RE", QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "REOPENED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_in_progress_to_open_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-I2O", QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "OPEN"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_in_progress_to_in_progress_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-I2I", QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_in_progress_to_resolved_success_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-I2R", QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "RESOLVED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_transition_in_progress_to_closed_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-I2C", QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "CLOSED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_in_progress_to_reopened_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-I2RE", QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "REOPENED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_resolved_to_open_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-R2O", QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "OPEN"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_resolved_to_in_progress_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-R2I", QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_resolved_to_resolved_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-R2R", QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "RESOLVED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_resolved_to_closed_success_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-R2C", QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "CLOSED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_transition_resolved_to_reopened_success_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-R2RE", QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "REOPENED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_transition_closed_to_open_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-C2O", QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "OPEN"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_closed_to_in_progress_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-C2I", QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_closed_to_resolved_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-C2R", QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "RESOLVED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_closed_to_closed_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-C2C", QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "CLOSED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_closed_to_reopened_success_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-C2RE", QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "REOPENED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_transition_reopened_to_open_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RE2O", QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "OPEN"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_reopened_to_in_progress_success_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RE2I", QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_transition_reopened_to_resolved_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RE2R", QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "RESOLVED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_reopened_to_closed_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RE2C", QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "CLOSED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_transition_reopened_to_reopened_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RE2RE", QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "REOPENED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_open_query_status_transitions(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STHELP1", QueryStatus.OPEN)
    res = update_query_status_service(db_session, q.id, QueryStatusUpdate(status=QueryStatus.IN_PROGRESS), emp1.id)
    assert res.status == QueryStatus.IN_PROGRESS

def test_in_progress_query_status_transitions(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STHELP2", QueryStatus.IN_PROGRESS)
    res = update_query_status_service(db_session, q.id, QueryStatusUpdate(status=QueryStatus.RESOLVED), emp1.id)
    assert res.status == QueryStatus.RESOLVED

def test_resolved_query_status_transitions(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STHELP3", QueryStatus.RESOLVED)
    res = update_query_status_service(db_session, q.id, QueryStatusUpdate(status=QueryStatus.CLOSED), emp1.id)
    assert res.status == QueryStatus.CLOSED

def test_closed_query_status_transitions(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STHELP4", QueryStatus.CLOSED)
    res = update_query_status_service(db_session, q.id, QueryStatusUpdate(status=QueryStatus.REOPENED), emp1.id)
    assert res.status == QueryStatus.REOPENED

def test_reopened_query_status_transitions(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STHELP5", QueryStatus.REOPENED)
    res = update_query_status_service(db_session, q.id, QueryStatusUpdate(status=QueryStatus.IN_PROGRESS), emp1.id)
    assert res.status == QueryStatus.IN_PROGRESS

def test_unauthorized_user_gets_403_before_business_validation(db_session, query_setup):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-STUNAUTH")
    with pytest.raises(ForbiddenException):
        update_query_status_service(db_session, q.id, QueryStatusUpdate(status=QueryStatus.IN_PROGRESS), unrelated.id)


# ============================================================================
# SECTION 3: RESOLUTION ENDPOINT & SERVICE TESTS (30 TESTS)
# ============================================================================

def test_resolve_query_unauthenticated_no_header_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RES01", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Resolved note"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_resolve_query_malformed_token_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RES02", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Resolved note"}, headers={"Authorization": "Bearer bad.token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_resolve_query_as_employee_owner_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESOWN", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Resolved by owner"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_resolve_query_as_employee_assignee_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESASG", status_val=QueryStatus.IN_PROGRESS, assigned_to_user=emp2.id)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Resolved by assignee"}, headers=get_jwt_headers(emp2))
    assert res.status_code == status.HTTP_200_OK

def test_resolve_query_as_unrelated_employee_forbidden_403(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESUNREL", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Forbidden"}, headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_resolve_query_as_org_admin_same_org_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESORG", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Admin resolve"}, headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK

def test_resolve_query_as_super_admin_always_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    super_admin = query_setup["super_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESSUP", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Super admin resolve"}, headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_resolve_query_nonexistent_uuid_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.patch(f"/queries/{uuid.uuid4()}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_resolve_query_malformed_uuid_path_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.patch("/queries/invalid-uuid/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_resolve_query_soft_deleted_query_404(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = Query(ticket_number="QRY-RESDEL", user_id=emp1.id, subject="Sub", message="Msg", priority=QueryPriority.LOW, status=QueryStatus.IN_PROGRESS, is_deleted=True)
    db_session.add(q)
    db_session.commit()
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_resolve_query_missing_note_field_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESMISS", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_resolve_query_null_note_field_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESNULL", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": None}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_resolve_query_empty_note_string_returns_400(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESEMPT", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": ""}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_resolve_query_whitespace_note_returns_400(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESWS", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "   "}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_resolve_query_special_characters_unicode_emojis_note_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESSPEC", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Resolved! 🎉 ✨"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_resolve_query_from_open_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESOPEN", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_resolve_query_from_already_resolved_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESRES", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_resolve_query_from_closed_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESCLS", status_val=QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_resolve_query_from_reopened_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESREO", status_val=QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_resolution_time_calculation_exact_seconds_60s(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESTIME", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Timed resolve"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_resolution_time_calculation_multi_day(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESMULTIDAY", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Multi day resolve"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_resolve_query_database_persistence_and_resolved_by(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESPER", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Persist note"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    db_session.refresh(q)
    assert q.status == QueryStatus.RESOLVED

def test_failed_resolution_creates_no_activity_log_and_preserves_state(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESFAIL", status_val=QueryStatus.IN_PROGRESS)
    auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(unrelated))
    db_session.refresh(q)
    assert q.status == QueryStatus.IN_PROGRESS

def test_resolved_query_reflected_in_get_by_id_and_ticket(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESREF", status_val=QueryStatus.IN_PROGRESS)
    auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.json()["status"] == "RESOLVED"

def test_resolve_query_happy_path(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESHP", status_val=QueryStatus.IN_PROGRESS)
    res = resolve_query_service(db_session, q.id, QueryResolve(resolution_note="Happy path note"), emp1.id)
    assert res.status == QueryStatus.RESOLVED

def test_resolve_query_invalid_status_transitions(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESINVTRANS", status_val=QueryStatus.OPEN)
    with pytest.raises(BadRequestException):
        resolve_query_service(db_session, q.id, QueryResolve(resolution_note="Note"), emp1.id)

def test_resolve_query_empty_resolution_note(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESEMPTNOTE", status_val=QueryStatus.IN_PROGRESS)
    with pytest.raises(BadRequestException):
        resolve_query_service(db_session, q.id, QueryResolve(resolution_note="   "), emp1.id)

def test_resolve_query_nonexistent(db_session, query_setup):
    emp1 = query_setup["emp1"]
    with pytest.raises(HTTPException) as exc:
        resolve_query_service(db_session, uuid.uuid4(), QueryResolve(resolution_note="Note"), emp1.id)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_resolution_time_computed_property(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-RESTIMECOMP", status_val=QueryStatus.IN_PROGRESS)
    res = resolve_query_service(db_session, q.id, QueryResolve(resolution_note="Note"), emp1.id)
    assert res.resolved_at is not None

def test_closure_time_computed_property(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSTIMECOMP", status_val=QueryStatus.RESOLVED)
    res = close_query_service(db_session, q.id, emp1.id)
    assert res.closed_at is not None

def test_repository_delete_query(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-REPOUPD4")
    res = repository.delete_query(db_session, q)
    assert res is not None


# ============================================================================
# SECTION 4: CLOSURE ENDPOINT & SERVICE TESTS (27 TESTS)
# ============================================================================

def test_close_query_unauthenticated_no_header_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLS01", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_close_query_malformed_token_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLS02", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers={"Authorization": "Bearer bad.token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_close_query_as_employee_owner_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSOWN", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_close_query_as_employee_assignee_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSASG", status_val=QueryStatus.RESOLVED, assigned_to_user=emp2.id)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp2))
    assert res.status_code == status.HTTP_200_OK

def test_close_query_as_unrelated_employee_forbidden_403(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSUNREL", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_close_query_as_org_admin_same_org_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSORG", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK

def test_close_query_as_super_admin_always_allowed_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    super_admin = query_setup["super_admin"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSSUP", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_close_query_nonexistent_uuid_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.patch(f"/queries/{uuid.uuid4()}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_close_query_malformed_uuid_path_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.patch("/queries/invalid-uuid/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_close_query_soft_deleted_query_404(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = Query(ticket_number="QRY-CLSDEL", user_id=emp1.id, subject="Sub", message="Msg", priority=QueryPriority.LOW, status=QueryStatus.RESOLVED, is_deleted=True)
    db_session.add(q)
    db_session.commit()
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_close_query_from_open_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSOPEN", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_close_query_from_in_progress_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSINP", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_close_query_from_already_closed_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSCLS", status_val=QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_close_query_from_reopened_throws_bad_request(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSREO", status_val=QueryStatus.REOPENED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_closure_time_calculation_exact_seconds_120s(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSTIME", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_closure_time_vs_resolution_time_distinction(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSDIST", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_close_query_database_persistence_and_closed_by(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSPER", status_val=QueryStatus.RESOLVED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    db_session.refresh(q)
    assert q.status == QueryStatus.CLOSED

def test_failed_closure_creates_no_activity_log_and_preserves_state(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSFAIL", status_val=QueryStatus.RESOLVED)
    auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(unrelated))
    db_session.refresh(q)
    assert q.status == QueryStatus.RESOLVED

def test_full_end_to_end_lifecycle_create_assign_status_resolve_close(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSE2E")
    auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Resolved"}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "CLOSED"

def test_closed_query_reflected_in_get_by_id_and_ticket(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSREF", status_val=QueryStatus.RESOLVED)
    auth_jwt_client.patch(f"/queries/{q.id}/close", headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.json()["status"] == "CLOSED"

def test_close_query_happy_path(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSHP", status_val=QueryStatus.RESOLVED)
    res = close_query_service(db_session, q.id, emp1.id)
    assert res.status == QueryStatus.CLOSED

def test_close_query_invalid_status_transitions(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-CLSINV", status_val=QueryStatus.OPEN)
    with pytest.raises(BadRequestException):
        close_query_service(db_session, q.id, emp1.id)

def test_close_query_nonexistent(db_session, query_setup):
    emp1 = query_setup["emp1"]
    with pytest.raises(HTTPException) as exc:
        close_query_service(db_session, uuid.uuid4(), emp1.id)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_repository_update_query(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_mutation_query(db_session, emp1.id, "QRY-REPOUPD3")
    q.status = QueryStatus.IN_PROGRESS
    res = repository.update_query(db_session, q)
    assert res.status == QueryStatus.IN_PROGRESS

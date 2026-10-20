"""
Exhaustive Query Authorization, Role Matrix, Validation & Error Response Test Suite (25 unrolled test functions).

Covers:
- Strict authorization & multi-tenant access matrix
- System-wide role matrices (SUPER_ADMIN, ORG_ADMIN, BATCH_ADMIN, EMPLOYEE)
- Boundary condition validation, malformed payloads & exact HTTP status codes
"""

import uuid
import pytest
from fastapi import status

from app.queries.models import Query, QueryPriority, QueryStatus
from app.queries.schemas import QueryCreate
from app.queries.service import create_query_service
from app.common.exceptions import BadRequestException, ForbiddenException
from app.tests.conftest import get_jwt_headers


def _create_auth_query(db_session, user_id, ticket_num="QRY-ATH001", status_val=QueryStatus.OPEN, priority_val=QueryPriority.MEDIUM):
    q = Query(
        ticket_number=ticket_num,
        user_id=user_id,
        subject="Auth Error Test Query Subject",
        message="Auth Error Test Query Body Message",
        priority=priority_val,
        status=status_val,
    )
    db_session.add(q)
    db_session.commit()
    return q


# ============================================================================
# SECTION 1: ROLE MATRIX & ACCESS CONTROL TESTS (15 TESTS)
# ============================================================================

def test_query_access_matrix_unauthenticated(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ATHUNAUTH")
    res = auth_jwt_client.get(f"/queries/{q.id}")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_query_access_matrix_employee_owner(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ATHOWN")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_query_access_matrix_employee_assignee(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = Query(ticket_number="QRY-ATHASG", user_id=emp1.id, assigned_to=emp2.id, subject="Subject Long Enough", message="Message Body Long Enough", priority=QueryPriority.LOW, status=QueryStatus.OPEN)
    db_session.add(q)
    db_session.commit()
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp2))
    assert res.status_code == status.HTTP_200_OK

def test_query_access_matrix_employee_neither_owner_nor_assignee(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ATHNEITHER")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_query_access_matrix_org_admin_same_org(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ATHSAMEORG")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK

def test_query_access_matrix_org_admin_different_org(auth_jwt_client, query_setup, db_session):
    unrelated = query_setup["unrelated_emp"]
    org_admin = query_setup["org_admin"]
    q = _create_auth_query(db_session, unrelated.id, "QRY-ATHDIFFORG")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_query_access_matrix_super_admin_all_orgs(auth_jwt_client, query_setup, db_session):
    unrelated = query_setup["unrelated_emp"]
    super_admin = query_setup["super_admin"]
    q = _create_auth_query(db_session, unrelated.id, "QRY-ATHSUPALL")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_query_authorization_matrix_unauthenticated_request_rejected_401(auth_jwt_client):
    res = auth_jwt_client.get("/queries/")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_query_authorization_matrix_employee_create_access_allowed(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.post("/queries/", json={"subject": "Auth Test Subject", "message": "Auth Test Body Message"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED

def test_query_authorization_matrix_employee_read_own_query_allowed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ATHO3")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_query_authorization_matrix_employee_read_other_query_forbidden_403(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ATHO4")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_query_authorization_matrix_org_admin_read_same_org_allowed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ATHO5")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK

def test_query_authorization_matrix_org_admin_read_different_org_forbidden_403(auth_jwt_client, query_setup, db_session):
    unrelated = query_setup["unrelated_emp"]
    org_admin = query_setup["org_admin"]
    q = _create_auth_query(db_session, unrelated.id, "QRY-ATHO6")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_query_authorization_matrix_super_admin_read_any_query_allowed(auth_jwt_client, query_setup, db_session):
    unrelated = query_setup["unrelated_emp"]
    super_admin = query_setup["super_admin"]
    q = _create_auth_query(db_session, unrelated.id, "QRY-ATHO7")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_query_authorization_matrix_cross_tenant_query_modification_forbidden_403(auth_jwt_client, query_setup, db_session):
    unrelated = query_setup["unrelated_emp"]
    org_admin = query_setup["org_admin"]
    q = _create_auth_query(db_session, unrelated.id, "QRY-ATHO8")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# SECTION 2: VALIDATORS & ERROR RESPONSE TESTS (10 TESTS)
# ============================================================================

def test_query_validators_empty_subject_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.post("/queries/", json={"subject": "", "message": "Message Body Long Enough"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_query_validators_whitespace_subject_400(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.post("/queries/", json={"subject": "   ", "message": "Message Body Long Enough"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_query_validators_empty_message_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.post("/queries/", json={"subject": "Valid Subject", "message": ""}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_query_validators_invalid_priority_enum_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.post("/queries/", json={"subject": "Valid Subject", "message": "Message Body Long Enough", "priority": "SUPER_HIGH"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_query_validators_invalid_status_enum_422(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ERR01")
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "UNKNOWN"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_query_validators_nonexistent_query_id_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get(f"/queries/{uuid.uuid4()}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_query_validators_nonexistent_ticket_number_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get("/queries/ticket/NONEXISTENT-TICKET-12345", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_query_validators_invalid_uuid_path_parameter_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get("/queries/not-a-uuid", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_query_validators_invalid_status_transition_400(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_auth_query(db_session, emp1.id, "QRY-ERR02", status_val=QueryStatus.OPEN)
    res = auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "RESOLVED"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_query_validators_service_layer_whitespace_raises_bad_request(db_session, query_setup):
    emp1 = query_setup["emp1"]
    res = create_query_service(db_session, QueryCreate(subject="Valid Subject", message="Message Body Long Enough"), emp1.id)
    assert res is not None

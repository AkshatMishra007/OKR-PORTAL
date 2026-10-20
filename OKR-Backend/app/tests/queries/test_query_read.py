"""
Exhaustive Query Read & Retrieval Test Suite (40 unrolled test functions).

Covers:
- GET /queries/{query_id} (Retrieval by UUID)
- GET /queries/ticket/{ticket_number} (Retrieval by Ticket Number)
- GET /queries/ (Global List Retrieval with Filtering, Sorting, Pagination)
- GET /queries/my (My Queries Retrieval)
- GET /queries/team (Team Queries Retrieval)
- Search, Filter & Read-Only Guarantees
"""

import uuid
from datetime import datetime, UTC
import pytest
from fastapi import HTTPException, status

from app.queries.models import Query, QueryPriority, QueryStatus
from app.queries.schemas import QueryListFilters
from app.queries.service import (
    get_query_service,
    get_query_by_ticket_service,
    get_queries_service,
    get_my_queries_service,
    get_team_queries_service,
)
from app.queries import repository
from app.organizations.models import Organization
from app.organization_members.models import OrganizationMember
from app.rbac.models import Role
from app.users.models import User
from app.tests.conftest import get_jwt_headers


def _create_query_helper(db_session, user_id, ticket_num="QRY-READ001", status_val=QueryStatus.OPEN, priority_val=QueryPriority.MEDIUM, assigned_to_user=None, subject_text="Subject", message_text="Message text"):
    q = Query(
        ticket_number=ticket_num,
        user_id=user_id,
        assigned_to=assigned_to_user,
        subject=subject_text,
        message=message_text,
        priority=priority_val,
        status=status_val,
    )
    db_session.add(q)
    db_session.commit()
    return q


# ============================================================================
# SECTION 1: GET /queries/{query_id} BY UUID (28 TESTS)
# ============================================================================

def test_get_query_by_id_unauthenticated_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID01")
    res = auth_jwt_client.get(f"/queries/{q.id}")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_query_by_id_malformed_token_401(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID02")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers={"Authorization": "Bearer bad.token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_query_by_id_invalid_token_401(auth_jwt_client):
    res = auth_jwt_client.get(f"/queries/{uuid.uuid4()}", headers={"Authorization": "Bearer invalid"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_query_by_id_valid_uuid_existing_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID04")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["id"] == str(q.id)

def test_get_query_by_id_nonexistent_uuid_404(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get(f"/queries/{uuid.uuid4()}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_get_query_by_id_malformed_uuid_string_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get("/queries/invalid-uuid", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_query_by_id_invalid_uuid_characters_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get("/queries/12345678-1234-1234-1234-123456789xyz", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_query_by_id_wrong_length_uuid_422(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    res = auth_jwt_client.get("/queries/12345", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_query_by_id_status_open(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID09", QueryStatus.OPEN)
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "OPEN"

def test_get_query_by_id_status_in_progress(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID10", QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "IN_PROGRESS"

def test_get_query_by_id_status_resolved(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID11", QueryStatus.RESOLVED)
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "RESOLVED"

def test_get_query_by_id_status_closed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID12", QueryStatus.CLOSED)
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "CLOSED"

def test_get_query_by_id_status_reopened(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID13", QueryStatus.REOPENED)
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "REOPENED"

def test_get_query_by_id_matrix_owner_allowed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID14")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_get_query_by_id_matrix_assignee_allowed(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID15", assigned_to_user=emp2.id)
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(emp2))
    assert res.status_code == status.HTTP_200_OK

def test_get_query_by_id_matrix_neither_owner_nor_assignee_forbidden_403(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID16")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_get_query_by_id_matrix_org_admin_same_org_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID17")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK

def test_get_query_by_id_matrix_super_admin_always_200(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    super_admin = query_setup["super_admin"]
    q = _create_query_helper(db_session, emp1.id, "QRY-RID18")
    res = auth_jwt_client.get(f"/queries/{q.id}", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

from app.common.exceptions import AppException, ForbiddenException

def test_get_query_by_id_matrix_org_admin_different_org_forbidden_403(db_session, query_setup):
    org_b = Organization(id=uuid.uuid4(), name="Org B", is_deleted=False)
    role_emp = db_session.query(Role).filter(Role.name == "EMPLOYEE").first()
    user_b = User(id=uuid.uuid4(), username="ub_rid19", email="ub19@test.com", password_hash="h", first_name="B", is_deleted=False)
    db_session.add_all([org_b, user_b])
    db_session.flush()
    mem_b = OrganizationMember(organization_id=org_b.id, user_id=user_b.id, role_id=role_emp.id, is_deleted=False, is_active=True)
    db_session.add(mem_b)
    db_session.commit()

    q_b = _create_query_helper(db_session, user_b.id, "QRY-RID19")
    org_admin_a = query_setup["org_admin"]

    with pytest.raises((HTTPException, ForbiddenException)):
        get_query_service(db_session, q_b.id, org_admin_a)

def test_get_query_by_id_batch_admin_different_batch_forbidden_403(db_session, query_setup):
    unrelated = query_setup["unrelated_emp"]
    batch_admin = query_setup["batch_admin"]
    q = _create_query_helper(db_session, unrelated.id, "QRY-RID21")
    with pytest.raises((HTTPException, ForbiddenException)):
        get_query_service(db_session, q.id, batch_admin)

def test_get_query_by_id_user_without_membership_forbidden_403(db_session, query_setup):
    emp1 = query_setup["emp1"]
    no_mem = User(id=uuid.uuid4(), username="nomem_rid", email="nomem@test.com", password_hash="h", first_name="No", is_deleted=False)
    db_session.add(no_mem)
    db_session.commit()
    q = _create_query_helper(db_session, emp1.id, "QRY-RID23")
    with pytest.raises((HTTPException, ForbiddenException)):
        get_query_service(db_session, q.id, no_mem)

def test_get_query_by_ticket_service_with_unauthorized_user_throws_403(db_session, query_setup):
    emp1 = query_setup["emp1"]
    unrelated = query_setup["unrelated_emp"]
    _create_query_helper(db_session, emp1.id, "QRY-TCK03")
    with pytest.raises((HTTPException, ForbiddenException)):
        get_query_by_ticket_service(db_session, "QRY-TCK03", current_user=unrelated)

def test_get_query_by_ticket_service_org_admin_different_org_forbidden_403(db_session, query_setup):
    unrelated = query_setup["unrelated_emp"]
    org_admin = query_setup["org_admin"]
    _create_query_helper(db_session, unrelated.id, "QRY-TCKDIF")
    with pytest.raises((HTTPException, ForbiddenException)):
        get_query_by_ticket_service(db_session, "QRY-TCKDIF", current_user=org_admin)

def test_list_queries_user_without_membership_forbidden_403(auth_jwt_client, db_session):
    no_mem = User(id=uuid.uuid4(), username="nomem_lst", email="nomemlst@test.com", password_hash="h", first_name="No", is_deleted=False)
    db_session.add(no_mem)
    db_session.commit()
    res = auth_jwt_client.get("/queries/", headers=get_jwt_headers(no_mem))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_repository_get_queries_direct_call(db_session):
    res, total = repository.get_queries(db=db_session, page=1, page_size=10)
    assert isinstance(res, list)

def test_query_filters_team_queries_repository_branches(db_session, query_setup):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    _create_query_helper(db_session, emp1.id, "QRY-FLTTEAM", assigned_to_user=emp1.id)
    res = get_team_queries_service(db_session, org_admin.id, QueryListFilters())
    assert res.total >= 1

def test_get_team_queries_service(db_session, query_setup):
    org_admin = query_setup["org_admin"]
    res = get_team_queries_service(db_session, org_admin.id, QueryListFilters())
    assert hasattr(res, "items")

def test_get_team_queries_user_without_membership_throws_404(db_session):
    no_mem = User(id=uuid.uuid4(), username="nomem_tm", email="nomemtm@test.com", password_hash="h", first_name="No", is_deleted=False)
    db_session.add(no_mem)
    db_session.commit()
    with pytest.raises((HTTPException, AppException)):
        get_team_queries_service(db_session, no_mem.id, QueryListFilters())





# ============================================================================
# SECTION 5: FILTER HELPER FUNCTION TESTS (15 TESTS)
# ============================================================================

def test_query_filters_status_and_priority(db_session, query_setup):
    emp1 = query_setup["emp1"]
    _create_query_helper(db_session, emp1.id, "QRY-FLT01", QueryStatus.OPEN, QueryPriority.HIGH, assigned_to_user=emp1.id)
    res = get_queries_service(db_session, QueryListFilters(status=QueryStatus.OPEN, priority=QueryPriority.HIGH))
    assert res.total >= 1

def test_query_filters_search_ticket_and_subject(db_session, query_setup):
    emp1 = query_setup["emp1"]
    _create_query_helper(db_session, emp1.id, "QRY-FLTSRCH", subject_text="Searchable Subject")
    res = get_queries_service(db_session, QueryListFilters(search="Searchable"))
    assert res.total >= 1

def test_query_filters_my_queries_repository_branches(db_session, query_setup):
    emp1 = query_setup["emp1"]
    _create_query_helper(db_session, emp1.id, "QRY-FLTMY", assigned_to_user=emp1.id)
    res = get_my_queries_service(db_session, emp1.id, QueryListFilters())
    assert res.total >= 1

def test_query_filters_team_queries_repository_branches(db_session, query_setup):
    emp1 = query_setup["emp1"]
    org_admin = query_setup["org_admin"]
    _create_query_helper(db_session, emp1.id, "QRY-FLTTEAM", assigned_to_user=emp1.id)
    res = get_team_queries_service(db_session, org_admin.id, QueryListFilters())
    assert res.total >= 1

def test_query_filters_pagination_edge_cases(db_session, query_setup):
    res = get_queries_service(db_session, QueryListFilters(page=100, page_size=10))
    assert res.items == []

def test_query_filters_pagination_api_validation(auth_jwt_client, query_setup):
    super_admin = query_setup["super_admin"]
    res = auth_jwt_client.get("/queries/?page=0", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_query_by_id_success(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-SUCC1")
    res = get_query_service(db_session, q.id, emp1)
    assert res.id == q.id

def test_get_query_by_id_nonexistent(db_session, query_setup):
    emp1 = query_setup["emp1"]
    with pytest.raises(HTTPException) as exc:
        get_query_service(db_session, uuid.uuid4(), emp1)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_query_by_id_deleted_query(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = Query(ticket_number="QRY-DELQ", user_id=emp1.id, subject="S", message="M", priority=QueryPriority.LOW, status=QueryStatus.OPEN, is_deleted=True)
    db_session.add(q)
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        get_query_service(db_session, q.id, emp1)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_query_by_ticket_number_success(db_session, query_setup):
    emp1 = query_setup["emp1"]
    q = _create_query_helper(db_session, emp1.id, "QRY-TCKNUMSUCC")
    res = get_query_by_ticket_service(db_session, "QRY-TCKNUMSUCC", current_user=emp1)
    assert res.id == q.id

def test_get_query_by_ticket_number_nonexistent(db_session, query_setup):
    emp1 = query_setup["emp1"]
    with pytest.raises(HTTPException) as exc:
        get_query_by_ticket_service(db_session, "NONEXISTENT-TICKET", current_user=emp1)
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_get_my_queries_service(db_session, query_setup):
    emp1 = query_setup["emp1"]
    res = get_my_queries_service(db_session, emp1.id, QueryListFilters())
    assert hasattr(res, "items")

def test_get_team_queries_service(db_session, query_setup):
    org_admin = query_setup["org_admin"]
    res = get_team_queries_service(db_session, org_admin.id, QueryListFilters())
    assert hasattr(res, "items")

def test_get_team_queries_user_without_membership_throws_404(db_session):
    no_mem = User(id=uuid.uuid4(), username="nomem_tm", email="nomemtm@test.com", password_hash="h", first_name="No", is_deleted=False)
    db_session.add(no_mem)
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        get_team_queries_service(db_session, no_mem.id, QueryListFilters())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND

def test_read_api_endpoints_via_client(auth_jwt_client, query_setup):
    super_admin = query_setup["super_admin"]
    res = auth_jwt_client.get("/queries/", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

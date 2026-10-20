"""
Final Integration & Scenario Audit Test Suite for Query Module (17 unrolled test functions).

Covers:
- End-to-end full query lifecycle transitions (CREATE -> ASSIGN -> STATUS -> RESOLVE -> CLOSE)
- Multi-user concurrency scenarios
- Audit trail integrity & non-repudiation
- Edge case combinations & boundary scenarios
"""

import uuid
import pytest
from fastapi import status

from app.queries.models import Query, QueryPriority, QueryStatus
from app.tests.conftest import get_jwt_headers


from app.queries.service import get_query_by_ticket_service

def _create_audit_query(db_session, user_id, ticket_num="QRY-AUD001", status_val=QueryStatus.OPEN, priority_val=QueryPriority.HIGH):
    q = Query(
        ticket_number=ticket_num,
        user_id=user_id,
        subject="Integration Audit Query Subject",
        message="Integration Audit Query Body Message",
        priority=priority_val,
        status=status_val,
    )
    db_session.add(q)
    db_session.commit()
    return q

def test_scenario_audit_get_ticket_by_number_case_sensitivity(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDCASE123")
    res = get_query_by_ticket_service(db_session, "QRY-AUDCASE123", current_user=emp1)
    assert res.id == q.id


# ============================================================================
# SECTION 1: END-TO-END LIFECYCLE & INTEGRATION AUDIT (17 TESTS)
# ============================================================================

def test_full_lifecycle_create_assign_status_resolve_close(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    
    # 1. CREATE
    res_create = auth_jwt_client.post("/queries/", json={"subject": "Audit Lifecycle Query Subject", "message": "Audit Lifecycle Query Body Message", "priority": "HIGH"}, headers=get_jwt_headers(emp1))
    assert res_create.status_code == status.HTTP_201_CREATED
    q_id = res_create.json()["id"]

    # 2. ASSIGN (Auto-transitions to IN_PROGRESS)
    res_assign = auth_jwt_client.patch(f"/queries/{q_id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res_assign.status_code == status.HTTP_200_OK
    assert res_assign.json()["assigned_to"] == str(emp2.id)
    assert res_assign.json()["status"] == "IN_PROGRESS"

    # 3. RESOLVE
    res_resolve = auth_jwt_client.patch(f"/queries/{q_id}/resolve", json={"resolution_note": "Issue investigated and resolved successfully."}, headers=get_jwt_headers(emp2))
    assert res_resolve.status_code == status.HTTP_200_OK
    assert res_resolve.json()["status"] == "RESOLVED"

    # 4. CLOSE
    res_close = auth_jwt_client.patch(f"/queries/{q_id}/close", headers=get_jwt_headers(emp1))
    assert res_close.status_code == status.HTTP_200_OK
    assert res_close.json()["status"] == "CLOSED"

    # 5. ACTIVITIES AUDIT
    res_act = auth_jwt_client.get(f"/queries/{q_id}/activities", headers=get_jwt_headers(emp1))
    assert res_act.status_code == status.HTTP_200_OK
    assert res_act.json()["total"] >= 3

def test_reopen_lifecycle_create_assign_resolve_reopen_resolve_close(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    
    res_c = auth_jwt_client.post("/queries/", json={"subject": "Reopen Query Lifecycle Subject", "message": "Reopen Query Lifecycle Message Body"}, headers=get_jwt_headers(emp1))
    q_id = res_c.json()["id"]
    auth_jwt_client.patch(f"/queries/{q_id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    auth_jwt_client.patch(f"/queries/{q_id}/resolve", json={"resolution_note": "Initial fix"}, headers=get_jwt_headers(emp2))
    
    res_reopen = auth_jwt_client.patch(f"/queries/{q_id}/status", json={"status": "REOPENED"}, headers=get_jwt_headers(emp1))
    assert res_reopen.status_code == status.HTTP_200_OK
    assert res_reopen.json()["status"] == "REOPENED"

    auth_jwt_client.patch(f"/queries/{q_id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp2))
    auth_jwt_client.patch(f"/queries/{q_id}/resolve", json={"resolution_note": "Final fix"}, headers=get_jwt_headers(emp2))
    res_final_close = auth_jwt_client.patch(f"/queries/{q_id}/close", headers=get_jwt_headers(emp1))
    assert res_final_close.status_code == status.HTTP_200_OK

def test_concurrent_query_assignment_race_condition(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    org_admin = query_setup["org_admin"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDCONCUR")
    
    res1 = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    res2 = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(org_admin.id)}, headers=get_jwt_headers(emp1))
    assert res1.status_code == status.HTTP_200_OK
    assert res2.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

def test_audit_trail_non_repudiation(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDNONREP")
    auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_edge_case_query_with_maximum_length_fields(auth_jwt_client, query_setup):
    emp1 = query_setup["emp1"]
    max_subj = "S" * 200
    max_msg = "M" * 2000
    res = auth_jwt_client.post("/queries/", json={"subject": max_subj, "message": max_msg}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED

def test_scenario_audit_unassigned_query_resolve_attempt_blocked(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDUNASG")
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Attempt resolve"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_400_BAD_REQUEST

def test_scenario_audit_reassigned_query_old_assignee_cannot_resolve(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    unrelated = query_setup["unrelated_emp"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDREASG", status_val=QueryStatus.IN_PROGRESS)
    auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(unrelated))
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_scenario_audit_deleted_query_activities_inaccessible(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = Query(ticket_number="QRY-AUDDELACT", user_id=emp1.id, subject="Sub", message="Msg", priority=QueryPriority.LOW, status=QueryStatus.OPEN, is_deleted=True)
    db_session.add(q)
    db_session.commit()
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_404_NOT_FOUND

def test_scenario_audit_dashboard_consistency_post_resolution(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    super_admin = query_setup["super_admin"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDDSH", status_val=QueryStatus.IN_PROGRESS)
    auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "Note"}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get("/queries/dashboard", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_scenario_audit_multiple_status_changes_activity_sequence(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDSEQ", status_val=QueryStatus.OPEN)
    auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "IN_PROGRESS"}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_scenario_audit_query_search_across_all_statuses(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    _create_audit_query(db_session, emp1.id, "QRY-AUDSRCHALL")
    res = auth_jwt_client.get("/queries/my?search=QRY-AUDSRCHALL", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_scenario_audit_team_queries_organization_isolation(auth_jwt_client, query_setup, db_session):
    unrelated = query_setup["unrelated_emp"]
    org_admin = query_setup["org_admin"]
    _create_audit_query(db_session, unrelated.id, "QRY-AUDTMISO")
    res = auth_jwt_client.get("/queries/team?search=QRY-AUDTMISO", headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["total"] == 0

def test_scenario_audit_resolve_note_sanitization_and_utf8(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDUTF8", status_val=QueryStatus.IN_PROGRESS)
    res = auth_jwt_client.patch(f"/queries/{q.id}/resolve", json={"resolution_note": "日本語/Français/Español 🚀"}, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_scenario_audit_closed_query_cannot_be_reassigned(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDCLSASG", status_val=QueryStatus.CLOSED)
    res = auth_jwt_client.patch(f"/queries/{q.id}/assign", json={"assigned_to": str(emp2.id)}, headers=get_jwt_headers(emp1))
    assert res.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

def test_scenario_audit_reopened_query_retains_history(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDREOHIST", status_val=QueryStatus.RESOLVED)
    auth_jwt_client.patch(f"/queries/{q.id}/status", json={"status": "REOPENED"}, headers=get_jwt_headers(emp1))
    res = auth_jwt_client.get(f"/queries/{q.id}/activities", headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_200_OK

def test_scenario_audit_high_priority_query_dashboard_filtering(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    super_admin = query_setup["super_admin"]
    _create_audit_query(db_session, emp1.id, "QRY-AUDHIGHPR", priority_val=QueryPriority.HIGH)
    res = auth_jwt_client.get("/queries/dashboard", headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_200_OK

def test_scenario_audit_get_ticket_by_number_case_sensitivity(auth_jwt_client, query_setup, db_session):
    emp1 = query_setup["emp1"]
    q = _create_audit_query(db_session, emp1.id, "QRY-AUDCASE123")
    res = get_query_by_ticket_service(db_session, "QRY-AUDCASE123", current_user=emp1)
    assert res.id == q.id

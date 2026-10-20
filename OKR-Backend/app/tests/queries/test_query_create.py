"""
Comprehensive Query Creation Test Suite (POST /queries/, 39 test functions).

Covers:
- Authentication & Role Access Matrix (Employee, Org Admin, Batch Admin, Super Admin)
- Minimal & Complete Request Payloads
- Required Field & Boundary Validations (Subject min/max, Message min/max)
- Priority Enum Validation & Defaults
- Ticket Number Sequential Generation & Fallback Logic
- Forged Body Fields Protection & Extra Fields Handling
- Database Persistence & Failed Request Atomicity
- Special Character Inputs (Quotes, Unicode, Emojis, SQL/HTML Strings)
- Immediate Retrieval & Cross-Endpoint Visibility
- QueryActivity Audit Side-Effect Creation
- Service-level & Repository-level Direct Unit Tests
"""

import uuid
from uuid import UUID
from datetime import datetime, UTC
import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.queries.models import Query, QueryPriority, QueryStatus
from app.queries.schemas import QueryCreate, QueryResponse
from app.queries.service import create_query_service, _generate_ticket_number, get_query_service, get_query_by_ticket_service
from app.queries import repository
from app.query_activity.models import QueryActivity, QueryActivityType
from app.tests.conftest import get_jwt_headers


# ============================================================================
# SECTION 1: AUTHENTICATION & ROLE ACCESS MATRIX
# ============================================================================

def test_create_query_unauthenticated_no_header_returns_401(auth_jwt_client):
    """Test POST /queries without Authorization header returns HTTP 401."""
    res = auth_jwt_client.post("/queries/", json={"subject": "Valid Subject", "message": "Valid message text"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_query_malformed_bearer_token_returns_401(auth_jwt_client):
    """Test POST /queries with malformed Bearer token returns HTTP 401."""
    headers = {"Authorization": "Bearer invalid.jwt.token"}
    res = auth_jwt_client.post("/queries/", json={"subject": "Valid Subject", "message": "Valid message text"}, headers=headers)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_query_as_employee_success_201(auth_jwt_client, query_setup):
    """Test Employee role can successfully create a query."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Employee Query Subject", "message": "Detailed support ticket message body."}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["subject"] == payload["subject"]
    assert data["message"] == payload["message"]
    assert data["status"] == "OPEN"


def test_create_query_as_org_admin_success_201(auth_jwt_client, query_setup):
    """Test Org Admin role can successfully create a query."""
    org_admin = query_setup["org_admin"]
    payload = {"subject": "Org Admin Query Subject", "message": "Detailed message from organization administrator."}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(org_admin))
    assert res.status_code == status.HTTP_201_CREATED


def test_create_query_as_batch_admin_success_201(auth_jwt_client, query_setup):
    """Test Batch Admin role can successfully create a query."""
    batch_admin = query_setup["batch_admin"]
    payload = {"subject": "Batch Admin Query Subject", "message": "Detailed message from batch administrator."}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(batch_admin))
    assert res.status_code == status.HTTP_201_CREATED


def test_create_query_as_super_admin_success_201(auth_jwt_client, query_setup):
    """Test Super Admin role can successfully create a query."""
    super_admin = query_setup["super_admin"]
    payload = {"subject": "Super Admin Query Subject", "message": "Detailed message from system super administrator."}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(super_admin))
    assert res.status_code == status.HTTP_201_CREATED


# ============================================================================
# SECTION 2: MINIMAL & COMPLETE VALID PAYLOADS
# ============================================================================

def test_create_query_minimal_valid_payload_success_201(auth_jwt_client, query_setup):
    """Test creation with minimum valid payload (only required subject and message)."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "MinSub", "message": "1234567890"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["priority"] == "MEDIUM"
    assert data["status"] == "OPEN"
    assert data["assigned_to"] is None


def test_create_query_complete_valid_payload_all_fields_201(auth_jwt_client, query_setup):
    """Test creation with complete valid payload including priority."""
    emp1 = query_setup["emp1"]
    payload = {
        "subject": "Complete Ticket Subject",
        "message": "Full detailed description of the technical issue.",
        "priority": "HIGH",
    }
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["subject"] == payload["subject"]
    assert data["message"] == payload["message"]
    assert data["priority"] == "HIGH"


def test_query_create_happy_path(db_session, query_setup):
    """Test valid query creation through service layer."""
    emp1 = query_setup["emp1"]
    data = QueryCreate(
        subject="High priority server down issue",
        message="The primary server is not responding to requests since 10 minutes.",
        priority=QueryPriority.HIGH,
    )

    query = create_query_service(
        db=db_session,
        query_data=data,
        current_user_id=emp1.id,
    )

    assert isinstance(query.id, uuid.UUID)
    assert query.ticket_number == "QRY-000001"
    assert query.user_id == emp1.id
    assert query.created_by == emp1.id
    assert query.subject == "High priority server down issue"
    assert query.message == "The primary server is not responding to requests since 10 minutes."
    assert query.priority == QueryPriority.HIGH
    assert query.status == QueryStatus.OPEN
    assert isinstance(query.submitted_at, datetime)

    db_query = db_session.query(Query).filter(Query.id == query.id).first()
    assert db_query is not None
    assert db_query.ticket_number == "QRY-000001"


# ============================================================================
# SECTION 3: SCHEMA & FIELD VALIDATIONS
# ============================================================================

def test_create_query_missing_subject_returns_422(auth_jwt_client, query_setup):
    """Test missing subject field returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"message": "Valid message text long enough"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_null_subject_returns_422(auth_jwt_client, query_setup):
    """Test null subject field returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": None, "message": "Valid message text long enough"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_missing_message_returns_422(auth_jwt_client, query_setup):
    """Test missing message field returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Valid Subject"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_null_message_returns_422(auth_jwt_client, query_setup):
    """Test null message field returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Valid Subject", "message": None}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_subject_boundary_min_4_chars_returns_422(auth_jwt_client, query_setup):
    """Test subject of length 4 (below min_length=5) returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "1234", "message": "Valid message body text"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_subject_boundary_min_5_chars_success_201(auth_jwt_client, query_setup):
    """Test subject of length 5 (exact min_length) succeeds."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "12345", "message": "Valid message body text"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED


def test_create_query_subject_boundary_max_255_chars_success_201(auth_jwt_client, query_setup):
    """Test subject of length 255 (exact max_length) succeeds."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "S" * 255, "message": "Valid message body text"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED


def test_create_query_subject_boundary_max_256_chars_returns_422(auth_jwt_client, query_setup):
    """Test subject of length 256 (above max_length=255) returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "S" * 256, "message": "Valid message body text"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_message_boundary_min_9_chars_returns_422(auth_jwt_client, query_setup):
    """Test message of length 9 (below min_length=10) returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Valid Subject", "message": "123456789"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_message_boundary_min_10_chars_success_201(auth_jwt_client, query_setup):
    """Test message of length 10 (exact min_length) succeeds."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Valid Subject", "message": "1234567890"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED


def test_query_create_schema_validation_min_max_length():
    """Test QueryCreate Pydantic schema validation rules directly."""
    with pytest.raises(ValidationError):
        QueryCreate(subject="Abc", message="Valid detailed message text.")

    with pytest.raises(ValidationError):
        QueryCreate(subject="Valid Subject Text", message="Short")

    with pytest.raises(ValidationError):
        QueryCreate(subject="A" * 256, message="Valid detailed message text.")


# ============================================================================
# SECTION 4: PRIORITY & DEFAULT VALUES
# ============================================================================

@pytest.mark.parametrize("priority_val", ["LOW", "MEDIUM", "HIGH", "URGENT"])
def test_create_query_all_valid_priorities(auth_jwt_client, query_setup, priority_val):
    """Test creation with every supported QueryPriority enum value."""
    emp1 = query_setup["emp1"]
    payload = {"subject": f"Priority {priority_val}", "message": "Message text long enough", "priority": priority_val}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["priority"] == priority_val


def test_create_query_invalid_priority_returns_422(auth_jwt_client, query_setup):
    """Test invalid priority string returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Valid Subject", "message": "Message text long enough", "priority": "SUPER_HIGH"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_query_lowercase_priority_returns_422(auth_jwt_client, query_setup):
    """Test lowercase priority string returns HTTP 422."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Valid Subject", "message": "Message text long enough", "priority": "low"}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_query_create_default_priority(db_session, query_setup):
    """Test priority defaults to QueryPriority.MEDIUM if not supplied."""
    emp1 = query_setup["emp1"]
    data = QueryCreate(
        subject="General inquiry about OKRs",
        message="Where can I view the quarterly company goals?",
    )

    query = create_query_service(
        db=db_session,
        query_data=data,
        current_user_id=emp1.id,
    )

    assert query.priority == QueryPriority.MEDIUM


def test_create_query_default_values_verification(auth_jwt_client, query_setup, db_session):
    """Verify all default and generated fields on created Query."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Defaults Verification", "message": "Checking defaults for newly created query."}
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED

    data = res.json()
    query_id = UUID(data["id"])

    db_q = db_session.query(Query).filter(Query.id == query_id).first()
    assert db_q is not None
    assert db_q.status == QueryStatus.OPEN
    assert db_q.priority == QueryPriority.MEDIUM
    assert db_q.user_id == emp1.id
    assert db_q.created_by == emp1.id
    assert db_q.assigned_to is None
    assert db_q.resolved_by is None
    assert db_q.closed_by is None
    assert db_q.resolved_at is None
    assert db_q.closed_at is None
    assert db_q.is_deleted is False


# ============================================================================
# SECTION 5: TICKET NUMBER GENERATION
# ============================================================================

def test_query_create_sequential_ticket_numbers(db_session, query_setup):
    """Test multiple created queries generate sequential ticket numbers (QRY-000001, QRY-000002, etc)."""
    emp1 = query_setup["emp1"]
    
    t1 = _generate_ticket_number(db_session)
    assert t1 == "QRY-000001"

    q1 = create_query_service(
        db=db_session,
        query_data=QueryCreate(subject="First Issue Title", message="Detailed message 1"),
        current_user_id=emp1.id,
    )
    assert q1.ticket_number == "QRY-000001"

    t2 = _generate_ticket_number(db_session)
    assert t2 == "QRY-000002"

    q2 = create_query_service(
        db=db_session,
        query_data=QueryCreate(subject="Second Issue Title", message="Detailed message 2"),
        current_user_id=emp1.id,
    )
    assert q2.ticket_number == "QRY-000002"


def test_ticket_number_generation_sequential(auth_jwt_client, query_setup):
    """Test sequential creation increments ticket numbers QRY-000001, QRY-000002... via API."""
    emp1 = query_setup["emp1"]

    res1 = auth_jwt_client.post("/queries/", json={"subject": "Seq Ticket 1", "message": "Message content 1"}, headers=get_jwt_headers(emp1))
    t1 = res1.json()["ticket_number"]

    res2 = auth_jwt_client.post("/queries/", json={"subject": "Seq Ticket 2", "message": "Message content 2"}, headers=get_jwt_headers(emp1))
    t2 = res2.json()["ticket_number"]

    num1 = int(t1.split("-")[1])
    num2 = int(t2.split("-")[1])
    assert num2 == num1 + 1


def test_query_create_ticket_number_fallback_on_invalid_format(db_session, query_setup):
    """Test ticket number generation fallback when previous ticket format is non-standard."""
    emp1 = query_setup["emp1"]

    malformed_query = Query(
        ticket_number="MALFORMED_TICKET",
        user_id=emp1.id,
        subject="Malformed ticket query",
        message="Testing fallback ticket generation.",
        priority=QueryPriority.LOW,
        status=QueryStatus.OPEN,
    )
    db_session.add(malformed_query)
    db_session.commit()

    next_ticket = _generate_ticket_number(db_session)
    assert next_ticket == "QRY-000001"


# ============================================================================
# SECTION 6: SECURITY & ATOMICITY
# ============================================================================

def test_create_query_forged_user_id_and_protected_fields_ignored(auth_jwt_client, query_setup, db_session):
    """Verify malicious request body attempting to forge user_id, status, assigned_to or ticket_number is ignored."""
    emp1 = query_setup["emp1"]
    emp2 = query_setup["emp2"]

    forged_payload = {
        "subject": "Forged Attempt",
        "message": "Attempting to inject user_id and status",
        "user_id": str(emp2.id),
        "status": "RESOLVED",
        "ticket_number": "QRY-FORGED999",
        "assigned_to": str(emp2.id),
        "is_deleted": True,
    }

    res = auth_jwt_client.post("/queries/", json=forged_payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED

    data = res.json()
    assert data["status"] == "OPEN"
    assert data["ticket_number"] != "QRY-FORGED999"

    db_q = db_session.query(Query).filter(Query.id == UUID(data["id"])).first()
    assert db_q.user_id == emp1.id
    assert db_q.assigned_to is None
    assert db_q.is_deleted is False


def test_failed_creation_no_database_persistence_or_activity_log(auth_jwt_client, query_setup, db_session):
    """Assert invalid request does not persist any query or activity log to database."""
    emp1 = query_setup["emp1"]
    count_queries_before = db_session.query(Query).count()
    count_activities_before = db_session.query(QueryActivity).count()

    invalid_payload = {"subject": "Short", "message": "Short"}
    res = auth_jwt_client.post("/queries/", json=invalid_payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    db_session.expire_all()
    count_queries_after = db_session.query(Query).count()
    count_activities_after = db_session.query(QueryActivity).count()

    assert count_queries_after == count_queries_before
    assert count_activities_after == count_activities_before


def test_create_query_special_inputs_quotes_unicode_emojis(auth_jwt_client, query_setup):
    """Test handling quotes, apostrophes, slashes, multiline, Unicode and emojis."""
    emp1 = query_setup["emp1"]
    payload = {
        "subject": "Subject with 'quotes' & \"double\" / \\ <script>",
        "message": "Line 1\nLine 2\nUnicode: 🚀 🔥 🎉 \t Tabbed & SQL ' OR '1'='1",
    }
    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["subject"] == payload["subject"]
    assert data["message"] == payload["message"]


# ============================================================================
# SECTION 7: VISIBILITY, AUDIT & REPEATED CREATION
# ============================================================================

def test_created_query_immediately_retrievable_via_id_and_list_apis(auth_jwt_client, query_setup):
    """Verify created query is immediately retrievable by ID and visible in list endpoints."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Visibility Check Query", "message": "Testing immediate visibility across APIs."}

    post_res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert post_res.status_code == status.HTTP_201_CREATED
    created = post_res.json()
    query_id = created["id"]
    ticket_number = created["ticket_number"]

    get_by_id_res = auth_jwt_client.get(f"/queries/{query_id}", headers=get_jwt_headers(emp1))
    assert get_by_id_res.status_code == status.HTTP_200_OK
    assert get_by_id_res.json()["ticket_number"] == ticket_number

    admin_list_res = auth_jwt_client.get("/queries/", headers=get_jwt_headers(query_setup["super_admin"]))
    assert admin_list_res.status_code == status.HTTP_200_OK
    all_ids = [q["id"] for q in admin_list_res.json()["items"]]
    assert query_id in all_ids


def test_create_query_activity_log_creation(auth_jwt_client, query_setup, db_session):
    """Verify that Query creation automatically creates a QueryActivity record."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Audit Activity Query", "message": "Detailed message for audit verification."}

    res = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    assert res.status_code == status.HTTP_201_CREATED
    query_id = UUID(res.json()["id"])

    act = db_session.query(QueryActivity).filter(QueryActivity.query_id == query_id).first()
    assert act is not None
    assert act.activity_type == QueryActivityType.CREATED
    assert act.description == "Query created."
    assert act.performed_by == emp1.id


def test_create_query_repeated_duplicate_content_allowed(auth_jwt_client, query_setup):
    """Test creating multiple queries with identical subject and message is permitted."""
    emp1 = query_setup["emp1"]
    payload = {"subject": "Identical Subject", "message": "Identical message body text"}

    res1 = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))
    res2 = auth_jwt_client.post("/queries/", json=payload, headers=get_jwt_headers(emp1))

    assert res1.status_code == status.HTTP_201_CREATED
    assert res2.status_code == status.HTTP_201_CREATED
    assert res1.json()["id"] != res2.json()["id"]
    assert res1.json()["ticket_number"] != res2.json()["ticket_number"]


# ============================================================================
# SECTION 8: DIRECT UNIT TESTS
# ============================================================================

def test_service_create_query_direct_unit_test(db_session, query_setup):
    """Direct unit test for create_query_service."""
    emp1 = query_setup["emp1"]
    dto = QueryCreate(subject="Direct Service Subject", message="Direct service message text", priority=QueryPriority.HIGH)

    res = create_query_service(db_session, query_data=dto, current_user_id=emp1.id)
    assert res.id is not None
    assert res.subject == "Direct Service Subject"
    assert res.priority == QueryPriority.HIGH
    assert res.user_id == emp1.id


def test_repository_create_query_direct_unit_test(db_session, query_setup):
    """Direct unit test for repository.create_query."""
    emp1 = query_setup["emp1"]
    q = Query(ticket_number="QRY-REPO001", user_id=emp1.id, subject="Repo Direct Subject", message="Repo direct message text", priority=QueryPriority.LOW, status=QueryStatus.OPEN)

    res = repository.create_query(db_session, q)
    assert res.id is not None
    assert res.ticket_number == "QRY-REPO001"

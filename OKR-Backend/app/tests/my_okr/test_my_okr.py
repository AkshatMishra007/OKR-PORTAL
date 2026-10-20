from datetime import date
import uuid
import pytest
from fastapi import status
from app.batches.models import Batch, Quarter, MeetingDay
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User
from app.auth.password import hash_password
from app.my_okr.schemas import OKRCreate, OKRUpdate
from app.my_okr import service
from app.common.exceptions import (
    ForbiddenException,
    OKRAlreadyExistsException,
    OKRNotFoundException,
    UserNotFoundException,
)


@pytest.fixture
def okr_setup(db_session, test_user):
    user = User(
        username=f"okr_user_{uuid.uuid4().hex[:6]}",
        email=f"okr_user_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Pass123!"),
        first_name="OKR",
        is_deleted=False,
    )
    db_session.add(user)

    org = Organization(name=f"OKR Org {uuid.uuid4().hex[:6]}", is_active=True, is_deleted=False)
    db_session.add(org)
    db_session.commit()

    role = db_session.query(Role).filter(Role.name == "ORG_ADMIN").first()
    if not role:
        role = Role(name="ORG_ADMIN", is_active=True, is_deleted=False)
        db_session.add(role)
        db_session.commit()

    org_member = OrganizationMember(
        user_id=user.id,
        organization_id=org.id,
        role_id=role.id,
        is_active=True,
        is_deleted=False,
    )
    test_user_member = OrganizationMember(
        user_id=test_user.id,
        organization_id=org.id,
        role_id=role.id,
        is_active=True,
        is_deleted=False,
    )
    db_session.add_all([org_member, test_user_member])

    batch = Batch(
        name="OKR Batch",
        quarter=Quarter.JFM,
        year=2026,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        organization_id=org.id,
        status="ACTIVE",
        is_active=True,
        is_deleted=False,
    )
    db_session.add(batch)
    db_session.commit()

    return {
        "user": user,
        "org": org,
        "role": role,
        "org_member": org_member,
        "batch": batch,
    }


def test_okr_service_and_repository(db_session, okr_setup, test_user):
    batch = okr_setup["batch"]
    member = okr_setup["org_member"]

    # Create OKR (STANDARD)
    create_data = OKRCreate(
        batch_id=batch.id,
        assigned_to=member.id,
        objective="Increase Sales",
        target="100.0",
        key_results="KR1, KR2",
        okr_type="STANDARD",
        tracker_enabled=False,
    )

    okr = service.create_okr(db_session, create_data, test_user)
    assert okr.id is not None
    assert okr.objective == "Increase Sales"

    # Duplicate creation exception
    with pytest.raises(OKRAlreadyExistsException):
        service.create_okr(db_session, create_data, test_user)

    # Get OKR by ID
    fetched = service.get_okr(db_session, okr.id, test_user)
    assert fetched.id == okr.id

    # Get OKRs List & Search
    res = service.get_okrs(db_session, test_user, batch_id=batch.id, assigned_to=member.id, search="Sales")
    assert res["pagination"]["total"] == 1
    assert len(res["data"]) == 1

    # Update OKR
    update_data = OKRUpdate(objective="Increase Sales Updated")
    updated = service.update_okr(db_session, okr.id, update_data, test_user)
    assert updated.objective == "Increase Sales Updated"

    # Delete OKR
    deleted = service.delete_okr(db_session, okr.id, test_user)
    assert deleted.is_deleted is True

    # Get Deleted OKR raises NotFound
    with pytest.raises(OKRNotFoundException):
        service.get_okr(db_session, okr.id, test_user)


def test_okr_validations_and_exceptions(db_session, okr_setup, test_user):
    batch = okr_setup["batch"]
    member = okr_setup["org_member"]
    invalid_id = uuid.uuid4()

    # Tracker validations
    with pytest.raises(ForbiddenException) as exc:
        service.create_okr(
            db_session,
            OKRCreate(
                batch_id=batch.id,
                assigned_to=member.id,
                objective="Obj2",
                okr_type="STANDARD",
                tracker_enabled=True,
            ),
            test_user,
        )
    assert "Tracker can only be enabled for Professional or Personal OKRs." in str(exc.value.message)

    # Allowed tracker types
    prof_okr = service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member.id,
            objective="Prof Obj",
            okr_type="Professional",
            tracker_enabled=True,
        ),
        test_user,
    )
    assert prof_okr.tracker_enabled is True

    pers_okr = service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member.id,
            objective="Personal Obj",
            okr_type="PERSONAL",
            tracker_enabled=True,
        ),
        test_user,
    )
    assert pers_okr.tracker_enabled is True

    # Invalid batch
    with pytest.raises(ForbiddenException) as exc3:
        service.create_okr(
            db_session,
            OKRCreate(
                batch_id=invalid_id,
                assigned_to=member.id,
                objective="Obj3",
                okr_type="STANDARD",
                tracker_enabled=False,
            ),
            test_user,
        )
    assert "Invalid batch" in str(exc3.value.message)

    # Invalid assigned member
    with pytest.raises(ForbiddenException) as exc4:
        service.create_okr(
            db_session,
            OKRCreate(
                batch_id=batch.id,
                assigned_to=invalid_id,
                objective="Obj4",
                okr_type="STANDARD",
                tracker_enabled=False,
            ),
            test_user,
        )
    assert "Assigned user is not a valid" in str(exc4.value.message)

    # Closed batch modification
    closed_batch = Batch(
        name="Closed Batch",
        quarter=Quarter.AMJ,
        year=2026,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.MONDAY,
        organization_id=okr_setup["org"].id,
        status="CLOSED",
        is_active=True,
        is_deleted=False,
    )
    db_session.add(closed_batch)
    db_session.commit()

    with pytest.raises(ForbiddenException) as exc5:
        service.create_okr(
            db_session,
            OKRCreate(
                batch_id=closed_batch.id,
                assigned_to=member.id,
                objective="Closed Obj",
                okr_type="STANDARD",
                tracker_enabled=False,
            ),
            test_user,
        )
    assert "batch is closed and read-only" in str(exc5.value.message)

    with pytest.raises(OKRNotFoundException):
        service.get_okr(db_session, invalid_id, test_user)


def test_okr_router(client, okr_setup, auth_headers):
    from app.main import app as fastapi_app
    from app.auth.dependencies import get_current_user

    user = okr_setup["user"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user

    batch = okr_setup["batch"]
    member = okr_setup["org_member"]
    headers = {"X-Organization-ID": str(okr_setup["org"].id), **auth_headers}

    # POST /okrs/
    res = client.post(
        "/okrs/",
        json={
            "batch_id": str(batch.id),
            "assigned_to": str(member.id),
            "objective": "Router OKR",
            "okr_type": "STANDARD",
            "tracker_enabled": False,
        },
        headers=headers,
    )
    assert res.status_code == status.HTTP_201_CREATED

    okr_id = res.json()["id"]

    # GET /okrs/
    res = client.get(f"/okrs/?batch_id={batch.id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # GET /okrs/{okr_id}
    res = client.get(f"/okrs/{okr_id}", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # PUT /okrs/{okr_id}
    res = client.put(
        f"/okrs/{okr_id}",
        json={"objective": "Router OKR Updated"},
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK

    # DELETE /okrs/{okr_id}
    res = client.delete(f"/okrs/{okr_id}", headers=headers)
    assert res.status_code == status.HTTP_204_NO_CONTENT


def test_get_okrs_by_user_service_and_endpoint(client, db_session, okr_setup, test_user, auth_headers):
    from app.main import app as fastapi_app
    from app.auth.dependencies import get_current_user

    user = okr_setup["user"]
    batch = okr_setup["batch"]
    member = okr_setup["org_member"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user
    headers = {"X-Organization-ID": str(okr_setup["org"].id), **auth_headers}

    # Create OKR for user
    okr1 = service.create_okr(
        db_session,
        OKRCreate(
            batch_id=batch.id,
            assigned_to=member.id,
            objective="User Specific OKR 1",
            okr_type="STANDARD",
            tracker_enabled=False,
        ),
        test_user,
    )

    # 1. Test service get_okrs_by_user
    res_service = service.get_okrs_by_user(db_session, user_id=user.id)
    assert res_service["pagination"]["total"] >= 1
    assert any(o.id == okr1.id for o in res_service["data"])

    # 2. Test service get_okrs_by_user with non-existent user
    non_existent_id = uuid.uuid4()
    with pytest.raises(UserNotFoundException):
        service.get_okrs_by_user(db_session, user_id=non_existent_id)

    # 3. Test API GET /okrs/user/{user_id}
    res_api = client.get(f"/okrs/user/{user.id}", headers=headers)
    assert res_api.status_code == status.HTTP_200_OK
    data = res_api.json()
    assert data["pagination"]["total"] >= 1
    assert any(item["id"] == str(okr1.id) for item in data["data"])

    # 4. Test API GET /okrs/user/{user_id} with search filter
    res_search = client.get(f"/okrs/user/{user.id}?search=Specific", headers=headers)
    assert res_search.status_code == status.HTTP_200_OK
    assert res_search.json()["pagination"]["total"] >= 1

    # 5. Test API GET /okrs/user/{user_id} for non-existent user (404)
    res_404 = client.get(f"/okrs/user/{non_existent_id}", headers=headers)
    assert res_404.status_code == status.HTTP_404_NOT_FOUND

    # 6. Test API GET /okrs/?user_id={user_id}
    res_query_param = client.get(f"/okrs/?user_id={user.id}", headers=headers)
    assert res_query_param.status_code == status.HTTP_200_OK
    assert res_query_param.json()["pagination"]["total"] >= 1



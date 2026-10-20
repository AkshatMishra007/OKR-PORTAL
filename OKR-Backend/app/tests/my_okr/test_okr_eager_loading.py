from datetime import date
import uuid
import pytest
from app.batches.models import Batch, BatchMember, MeetingDay, Quarter
from app.my_okr import repository as okr_repository, service as okr_service
from app.my_okr.schemas import OKRCreate, OKRResponse
from app.organization_members.models import OrganizationMember
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


@pytest.fixture
def eager_load_setup(db_session):
    org = Organization(name=f"Eager Org {uuid.uuid4().hex[:6]}", is_active=True, is_deleted=False)
    db_session.add(org)
    db_session.commit()

    role = Role(name="EMPLOYEE", is_active=True, is_deleted=False)
    db_session.add(role)
    db_session.commit()

    user = User(
        username=f"eager_user_{uuid.uuid4().hex[:6]}",
        email=f"eager_{uuid.uuid4().hex[:6]}@test.com",
        password_hash="hashed_pw",
        first_name="Eager",
        last_name="Tester",
        is_deleted=False,
    )
    db_session.add(user)
    db_session.commit()

    batch = Batch(
        name="Eager Batch Q1",
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

    member = OrganizationMember(
        user_id=user.id,
        organization_id=org.id,
        role_id=role.id,
        is_active=True,
        is_deleted=False,
    )
    bm = BatchMember(
        batch_id=batch.id,
        user_id=user.id,
        role_id=role.id,
        is_active=True,
        is_deleted=False,
    )
    db_session.add_all([member, bm])
    db_session.commit()

    create_data = OKRCreate(
        batch_id=batch.id,
        assigned_to=member.id,
        objective="Eager Load Objective",
        target="100.0",
        key_results="KR1, KR2",
        okr_type="PROFESSIONAL",
        tracker_enabled=True,
    )
    okr = okr_service.create_okr(db_session, create_data, user)

    return {
        "org": org,
        "role": role,
        "user": user,
        "batch": batch,
        "member": member,
        "okr": okr,
    }


def test_get_okr_by_id_eager_loads_relationships(db_session, eager_load_setup):
    okr_id = eager_load_setup["okr"].id
    fetched_okr = okr_repository.get_okr_by_id(db_session, okr_id)

    assert fetched_okr is not None
    assert fetched_okr.id == okr_id

    # Verify Batch & Batch Organization eager loading
    assert fetched_okr.batch is not None
    assert fetched_okr.batch.name == "Eager Batch Q1"
    assert fetched_okr.batch.organization is not None
    assert fetched_okr.batch.organization.name == eager_load_setup["org"].name

    # Verify Assignee, User, Role eager loading
    assert fetched_okr.assignee is not None
    assert fetched_okr.assignee.user is not None
    assert fetched_okr.assignee.user.email == eager_load_setup["user"].email
    assert fetched_okr.assignee.role is not None
    assert fetched_okr.assignee.role.name == "EMPLOYEE"

    # Verify Organization property getters
    assert fetched_okr.organization is not None
    assert fetched_okr.organization.id == eager_load_setup["org"].id
    assert fetched_okr.organization_id == eager_load_setup["org"].id


def test_get_okrs_eager_loading_and_pagination(db_session, eager_load_setup):
    org_id = eager_load_setup["org"].id
    okrs, total = okr_repository.get_okrs(db_session, organization_id=org_id, page=1, size=10)

    assert total >= 1
    assert len(okrs) >= 1

    first_okr = okrs[0]
    assert first_okr.batch is not None
    assert first_okr.batch.organization is not None
    assert first_okr.assignee is not None
    assert first_okr.assignee.user is not None


def test_okr_response_pydantic_serialization(db_session, eager_load_setup):
    okr_id = eager_load_setup["okr"].id
    fetched_okr = okr_repository.get_okr_by_id(db_session, okr_id)

    response_model = OKRResponse.model_validate(fetched_okr)
    serialized = response_model.model_dump(mode="json")

    # Original UUID fields present
    assert serialized["batch_id"] == str(eager_load_setup["batch"].id)
    assert serialized["assigned_to"] == str(eager_load_setup["user"].id)
    assert serialized["organization_id"] == str(eager_load_setup["org"].id)

    # Nested eagerly loaded object representations present without duplicates
    assert serialized["batch"] is not None
    assert serialized["batch"]["id"] == str(eager_load_setup["batch"].id)
    assert serialized["batch"]["name"] == "Eager Batch Q1"

    assert serialized["assignee"] is not None
    assert serialized["assignee"]["id"] == str(eager_load_setup["member"].id)
    assert serialized["assignee"]["user_id"] == str(eager_load_setup["user"].id)
    assert serialized["assignee"]["user"]["email"] == eager_load_setup["user"].email

    assert serialized["organization"] is not None
    assert serialized["organization"]["id"] == str(eager_load_setup["org"].id)
    assert serialized["organization"]["name"] == eager_load_setup["org"].name

    # Duplicate top-level and nested fields are removed
    assert "assigned_user" not in serialized
    assert "batch" not in serialized["assignee"]
    assert "organization" not in serialized["assignee"]

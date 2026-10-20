import uuid
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from app.batches.models import Batch, MeetingDay, Quarter
from app.batches.schemas import BatchCreate
from app.batches.service import BatchService
from app.common.exceptions import (
    AppException,
    BatchAlreadyExistsException,
    OrganizationNotFoundException,
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock query for _get_batch_members_lists
    db.query.return_value.options.return_value.filter.return_value.all.return_value = []
    return db


@pytest.fixture
def current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_superuser = True
    return user


@patch("app.batches.service.batch_repository.create_batch_member")
@patch("app.batches.service.batch_repository.get_batch_member")
@patch("app.batches.service.organization_member_repository.get_member_by_user_and_organization")
@patch("app.batches.service.batch_repository.get_employee_membership_in_other_batch")
@patch("app.batches.service.batch_repository.create_batch")
@patch("app.batches.service.user_service.get_user_by_id")
@patch("app.batches.service.rbac_repository.get_role_by_name")
@patch("app.batches.service.batch_repository.get_batch_by_name_year_and_quarter")
@patch("app.batches.service.organization_repository.get_organization_by_id")
def test_scenario_a_create_batch_with_employee(
    mock_get_org,
    mock_get_existing_batch,
    mock_get_role_by_name,
    mock_get_user,
    mock_create_batch_repo,
    mock_get_employee_in_other,
    mock_get_org_member,
    mock_get_batch_member,
    mock_create_batch_member,
    mock_db,
    current_user,
):
    """
    Scenario A:
    Request with USER1 in batch_users (Employee).
    Result: BatchMember created with (USER1, BATCH1, Employee).
    """
    org_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    batch_id = uuid.uuid4()
    emp_role_id = uuid.uuid4()

    mock_get_org.return_value = MagicMock(id=org_id)
    mock_get_existing_batch.return_value = None
    mock_get_role_by_name.return_value = MagicMock(id=emp_role_id, name="Employee")
    mock_get_user.return_value = MagicMock(id=user1_id)
    mock_get_org_member.return_value = MagicMock(id=uuid.uuid4(), user_id=user1_id, organization_id=org_id, is_active=True, is_deleted=False)
    mock_get_employee_in_other.return_value = None  # Not in another batch
    mock_get_batch_member.return_value = None

    created_batch = MagicMock(id=batch_id, organization_id=org_id)
    mock_create_batch_repo.return_value = created_batch

    service = BatchService(mock_db)
    batch_data = BatchCreate(
        organization_id=org_id,
        name="Q1",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user1_id],
        batch_admins=[],
    )

    result = service.create_batch(batch_data, current_user)

    assert result == created_batch
    mock_create_batch_member.assert_called_once_with(
        db=mock_db,
        batch_id=batch_id,
        user_id=user1_id,
        role_id=emp_role_id,
        created_by=current_user.id,
    )
    mock_db.commit.assert_called_once()


@patch("app.batches.service.batch_repository.create_batch_member")
@patch("app.batches.service.batch_repository.get_batch_member")
@patch("app.batches.service.organization_member_repository.get_member_by_user_and_organization")
@patch("app.batches.service.batch_repository.create_batch")
@patch("app.batches.service.user_service.get_user_by_id")
@patch("app.batches.service.rbac_repository.get_role_by_name")
@patch("app.batches.service.batch_repository.get_batch_by_name_year_and_quarter")
@patch("app.batches.service.organization_repository.get_organization_by_id")
def test_scenario_b_and_e_create_another_batch_with_batch_admin(
    mock_get_org,
    mock_get_existing_batch,
    mock_get_role_by_name,
    mock_get_user,
    mock_create_batch_repo,
    mock_get_org_member,
    mock_get_batch_member,
    mock_create_batch_member,
    mock_db,
    current_user,
):
    """
    Scenario B & E:
    Batch Admin can belong to multiple batches.
    USER1 can be Batch Admin in Batch 2 even if already an Employee in Batch 1 or Batch Admin in Batch 1.
    First row is never overwritten.
    """
    org_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    batch2_id = uuid.uuid4()
    batch_admin_role_id = uuid.uuid4()

    mock_get_org.return_value = MagicMock(id=org_id)
    mock_get_existing_batch.return_value = None
    mock_get_role_by_name.return_value = MagicMock(id=batch_admin_role_id, name="Batch Admin")
    mock_get_user.return_value = MagicMock(id=user1_id)
    mock_get_org_member.return_value = MagicMock(id=uuid.uuid4(), user_id=user1_id, organization_id=org_id, is_active=True, is_deleted=False)
    mock_get_batch_member.return_value = None

    created_batch2 = MagicMock(id=batch2_id, organization_id=org_id)
    mock_create_batch_repo.return_value = created_batch2

    service = BatchService(mock_db)
    batch_data = BatchCreate(
        organization_id=org_id,
        name="Q2",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[],
        batch_admins=[user1_id],
    )

    result = service.create_batch(batch_data, current_user)

    assert result == created_batch2
    mock_create_batch_member.assert_called_once_with(
        db=mock_db,
        batch_id=batch2_id,
        user_id=user1_id,
        role_id=batch_admin_role_id,
        created_by=current_user.id,
    )
    mock_db.commit.assert_called_once()


@patch("app.batches.service.organization_member_repository.get_member_by_user_and_organization")
@patch("app.batches.service.batch_repository.get_employee_membership_in_other_batch")
@patch("app.batches.service.user_service.get_user_by_id")
@patch("app.batches.service.rbac_repository.get_role_by_name")
@patch("app.batches.service.batch_repository.get_batch_by_name_year_and_quarter")
@patch("app.batches.service.organization_repository.get_organization_by_id")
def test_scenario_c_employee_already_in_another_batch_rejected(
    mock_get_org,
    mock_get_existing_batch,
    mock_get_role_by_name,
    mock_get_user,
    mock_get_employee_in_other,
    mock_get_org_member,
    mock_db,
    current_user,
):
    """
    Scenario C (Rule 2):
    Try adding USER1 as Employee to Batch 2 when USER1 is already Employee in Batch 1.
    Must be rejected with AppException.
    """
    org_id = uuid.uuid4()
    user1_id = uuid.uuid4()
    emp_role_id = uuid.uuid4()

    mock_get_org.return_value = MagicMock(id=org_id)
    mock_get_existing_batch.return_value = None
    mock_get_role_by_name.return_value = MagicMock(id=emp_role_id, name="Employee")
    mock_get_user.return_value = MagicMock(id=user1_id)
    mock_get_org_member.return_value = MagicMock(id=uuid.uuid4(), user_id=user1_id, organization_id=org_id, is_active=True, is_deleted=False)
    # Existing Employee record in Batch 1
    mock_get_employee_in_other.return_value = MagicMock(id=uuid.uuid4(), user_id=user1_id, role_id=emp_role_id)

    service = BatchService(mock_db)
    batch_data = BatchCreate(
        organization_id=org_id,
        name="Q2",
        year=2026,
        quarter=Quarter.AMJ,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user1_id],
        batch_admins=[],
    )

    with pytest.raises(AppException) as exc_info:
        service.create_batch(batch_data, current_user)

    assert "Employee is already assigned to another batch." in str(exc_info.value)


def test_rule_5_user_cannot_be_both_employee_and_admin_in_same_batch(mock_db, current_user):
    """
    Scenario D / Rule 5:
    batch_users = [USER1] and batch_admins = [USER1] in same request.
    Must be rejected immediately before creating anything.
    """
    org_id = uuid.uuid4()
    user1_id = uuid.uuid4()

    service = BatchService(mock_db)
    batch_data = BatchCreate(
        organization_id=org_id,
        name="Q1",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user1_id],
        batch_admins=[user1_id],
    )

    with patch("app.batches.service.organization_repository.get_organization_by_id") as mock_get_org, \
         patch("app.batches.service.batch_repository.get_batch_by_name_year_and_quarter") as mock_get_existing:
        mock_get_org.return_value = MagicMock(id=org_id)
        mock_get_existing.return_value = None

        with pytest.raises(AppException) as exc_info:
            service.create_batch(batch_data, current_user)

        assert "cannot be both Employee and Batch Admin" in str(exc_info.value)


@patch("app.batches.service.batch_repository.create_batch_member")
@patch("app.batches.service.batch_repository.get_batch_member")
@patch("app.batches.service.organization_member_repository.get_member_by_user_and_organization")
@patch("app.batches.service.batch_repository.get_employee_membership_in_other_batch")
@patch("app.batches.service.batch_repository.create_batch")
@patch("app.batches.service.user_service.get_user_by_id")
@patch("app.batches.service.rbac_repository.get_role_by_name")
@patch("app.batches.service.batch_repository.get_batch_by_name_year_and_quarter")
@patch("app.batches.service.organization_repository.get_organization_by_id")
def test_transaction_rollback_on_member_creation_failure(
    mock_get_org,
    mock_get_existing_batch,
    mock_get_role_by_name,
    mock_get_user,
    mock_create_batch_repo,
    mock_get_employee_in_other,
    mock_get_org_member,
    mock_get_batch_member,
    mock_create_batch_member,
    mock_db,
    current_user,
):
    """
    Atomicity Test:
    If any member creation throws an exception, the entire transaction is rolled back.
    """
    org_id = uuid.uuid4()
    user1_id = uuid.uuid4()

    mock_get_org.return_value = MagicMock(id=org_id)
    mock_get_existing_batch.return_value = None
    mock_get_role_by_name.return_value = MagicMock(id=uuid.uuid4(), name="Employee")
    mock_get_user.return_value = MagicMock(id=user1_id)
    mock_get_org_member.return_value = MagicMock(id=uuid.uuid4(), user_id=user1_id, organization_id=org_id, is_active=True, is_deleted=False)
    mock_get_employee_in_other.return_value = None
    mock_get_batch_member.return_value = None

    mock_create_batch_repo.return_value = MagicMock(id=uuid.uuid4(), organization_id=org_id)
    mock_create_batch_member.side_effect = RuntimeError("Database insertion error")

    service = BatchService(mock_db)
    batch_data = BatchCreate(
        organization_id=org_id,
        name="Q1",
        year=2026,
        quarter=Quarter.JFM,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        meeting_day=MeetingDay.MONDAY,
        batch_users=[user1_id],
        batch_admins=[],
    )

    with pytest.raises(RuntimeError):
        service.create_batch(batch_data, current_user)

    mock_db.rollback.assert_called_once()

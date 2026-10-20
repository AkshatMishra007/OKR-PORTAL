import uuid
from unittest.mock import MagicMock, patch
import pytest

from app.batch_members.models import BatchMember
from app.batch_members.schemas import (
    BatchMemberCreate,
    BatchMemberUpdate,
)
from app.batch_members.service import (
    create_batch_member_service,
    delete_batch_member_service,
    get_batch_member_service,
    list_batch_members_service,
    update_batch_member_service,
)
from app.common.exceptions import (
    AppException,
    BatchMemberNotFoundException,
    BatchNotFoundException,
    RoleNotFoundException,
    UserNotFoundException,
)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def sample_ids():
    return {
        "batch_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "role_id": uuid.uuid4(),
        "org_id": uuid.uuid4(),
    }


# ==========================================================
# Service Tests
# ==========================================================

@patch("app.batch_members.service.batch_member_repository.create_batch_member")
@patch("app.batch_members.service.rbac_repository.get_role_by_id")
@patch("app.batch_members.service.organization_member_repository.get_member_by_user_and_organization")
@patch("app.batch_members.service.user_service.get_user_by_id")
@patch("app.batch_members.service._validate_batch_member_access")
@patch("app.batch_members.service.batch_repository.get_batch_by_id")
def test_create_batch_member_success(
    mock_get_batch,
    mock_val_access,
    mock_get_user,
    mock_get_org_member,
    mock_get_role,
    mock_create_member,
    mock_db,
    sample_ids,
):
    mock_get_batch.return_value = MagicMock(id=sample_ids["batch_id"], organization_id=sample_ids["org_id"])
    mock_get_user.return_value = MagicMock(id=sample_ids["user_id"])
    mock_get_org_member.return_value = MagicMock(is_active=True, is_deleted=False)
    role_mock = MagicMock(id=sample_ids["role_id"])
    role_mock.name = "Employee"
    mock_get_role.return_value = role_mock

    created = BatchMember(
        id=uuid.uuid4(),
        batch_id=sample_ids["batch_id"],
        user_id=sample_ids["user_id"],
        role_id=sample_ids["role_id"],
        is_active=True,
        is_deleted=False,
    )
    mock_create_member.return_value = created

    with patch("app.batch_members.service.batch_member_repository.get_employee_membership_in_other_batch", return_value=None):
        payload = BatchMemberCreate(
            batch_id=sample_ids["batch_id"],
            user_id=sample_ids["user_id"],
            role_id=sample_ids["role_id"],
        )
        result = create_batch_member_service(mock_db, payload)
        assert result.batch_id == sample_ids["batch_id"]
        assert result.user_id == sample_ids["user_id"]


@patch("app.batch_members.service.rbac_repository.get_role_by_id")
@patch("app.batch_members.service.organization_member_repository.get_member_by_user_and_organization")
@patch("app.batch_members.service.user_service.get_user_by_id")
@patch("app.batch_members.service._validate_batch_member_access")
@patch("app.batch_members.service.batch_repository.get_batch_by_id")
def test_create_batch_member_employee_already_in_other_batch(
    mock_get_batch,
    mock_val_access,
    mock_get_user,
    mock_get_org_member,
    mock_get_role,
    mock_db,
    sample_ids,
):
    mock_get_batch.return_value = MagicMock(id=sample_ids["batch_id"], organization_id=sample_ids["org_id"])
    mock_get_user.return_value = MagicMock(id=sample_ids["user_id"])
    mock_get_org_member.return_value = MagicMock(is_active=True, is_deleted=False)
    role_mock = MagicMock(id=sample_ids["role_id"])
    role_mock.name = "Employee"
    mock_get_role.return_value = role_mock

    with patch("app.batch_members.service.batch_member_repository.get_employee_membership_in_other_batch", return_value=MagicMock()):
        payload = BatchMemberCreate(
            batch_id=sample_ids["batch_id"],
            user_id=sample_ids["user_id"],
            role_id=sample_ids["role_id"],
        )
        with pytest.raises(AppException, match="Employee is already assigned to another batch."):
            create_batch_member_service(mock_db, payload)


@patch("app.batch_members.service.user_service.get_user_by_id")
@patch("app.batch_members.service._validate_batch_member_access")
@patch("app.batch_members.service.batch_repository.get_batch_by_id")
def test_create_batch_member_user_not_in_org(
    mock_get_batch,
    mock_val_access,
    mock_get_user,
    mock_db,
    sample_ids,
):
    mock_get_batch.return_value = MagicMock(id=sample_ids["batch_id"], organization_id=sample_ids["org_id"])
    mock_get_user.return_value = MagicMock(id=sample_ids["user_id"])

    with patch("app.batch_members.service.organization_member_repository.get_member_by_user_and_organization", return_value=None):
        payload = BatchMemberCreate(
            batch_id=sample_ids["batch_id"],
            user_id=sample_ids["user_id"],
            role_id=sample_ids["role_id"],
        )
        with pytest.raises(AppException, match="User is not an active member of this organization."):
            create_batch_member_service(mock_db, payload)


@patch("app.batch_members.service._validate_batch_member_access")
@patch("app.batch_members.service.batch_member_repository.get_batch_member_by_id")
def test_get_batch_member_service(
    mock_get_member,
    mock_val_access,
    mock_db,
    sample_ids,
):
    member_id = uuid.uuid4()
    mock_get_member.return_value = MagicMock(id=member_id, batch_id=sample_ids["batch_id"])

    result = get_batch_member_service(mock_db, member_id)
    assert result.id == member_id


@patch("app.batch_members.service._validate_batch_member_access")
@patch("app.batch_members.service.batch_member_repository.get_batch_member_by_id")
def test_update_batch_member_role_change_rejected(
    mock_get_member,
    mock_val_access,
    mock_db,
    sample_ids,
):
    member_id = uuid.uuid4()
    mock_get_member.return_value = MagicMock(id=member_id, batch_id=sample_ids["batch_id"], role_id=uuid.uuid4())

    new_role_id = uuid.uuid4()
    payload = BatchMemberUpdate(role_id=new_role_id)

    with pytest.raises(AppException, match="Role change for existing batch member is not supported."):
        update_batch_member_service(mock_db, member_id, payload)


@patch("app.batch_members.service.batch_member_repository.soft_delete_batch_member")
@patch("app.batch_members.service._validate_batch_member_access")
@patch("app.batch_members.service.batch_member_repository.get_batch_member_by_id")
def test_delete_batch_member_service(
    mock_get_member,
    mock_val_access,
    mock_soft_delete,
    mock_db,
    sample_ids,
):
    member_id = uuid.uuid4()
    mock_member = MagicMock(id=member_id, batch_id=sample_ids["batch_id"])
    mock_get_member.return_value = mock_member
    mock_soft_delete.return_value = mock_member

    result = delete_batch_member_service(mock_db, member_id)
    mock_soft_delete.assert_called_once()
    assert result == mock_member

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import (
    AppException,
    OrganizationNotFoundException,
    UserNotFoundException,
    RoleNotFoundException,
    OrganizationMemberAlreadyExistsException,
    OrganizationMemberNotFoundException,
)

from app.organization_members.schemas import (
    OrganizationMemberCreate,
    OrganizationMemberUpdate,
)

from app.organization_members.service import (
    create_member_service,
    get_member_service,
    list_members_service,
    update_member_service,
    delete_member_service,
)

from app.organization_members.models import OrganizationMember

# ==========================================================
# Create Member Tests
# ==========================================================


@patch("app.organization_members.service.repository.create_member")
@patch("app.organization_members.service.repository.get_member_by_user_and_organization")
@patch("app.organization_members.service.rbac_repository.get_role_by_id")
@patch("app.organization_members.service.user_service.get_user_by_id")
@patch("app.organization_members.service.organization_repository.get_organization_by_id")
def test_tc_01_create_member_success(
    mock_get_org,
    mock_get_user,
    mock_get_role,
    mock_get_member,
    mock_create_member,
):
    """
    Verify member is created successfully.
    """

    organization_id = uuid.uuid4()
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()

    payload = OrganizationMemberCreate(
        organization_id=organization_id,
        user_id=user_id,
        role_id=role_id,
    )

    mock_db = MagicMock()

    mock_get_org.return_value = MagicMock(id=organization_id)
    mock_get_user.return_value = MagicMock(id=user_id)
    mock_get_role.return_value = MagicMock(id=role_id, name="member", requires_batch=None)
    mock_get_member.return_value = None

    created_member = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        role_id=role_id,
    )

    mock_create_member.return_value = created_member

    result = create_member_service(
        mock_db,
        payload,
    )

    mock_create_member.assert_called_once()

    assert result.organization_id == organization_id
    assert result.user_id == user_id
    assert result.role_id == role_id


@patch("app.organization_members.service.organization_repository.get_organization_by_id")
def test_tc_02_create_member_organization_not_found(mock_get_org):
    """
    Verify exception when organization does not exist.
    """

    payload = OrganizationMemberCreate(
        organization_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_id=uuid.uuid4(),
    )

    mock_db = MagicMock()
    mock_get_org.return_value = None

    with pytest.raises(OrganizationNotFoundException):
        create_member_service(
            mock_db,
            payload,
        )


@patch("app.organization_members.service.user_service.get_user_by_id")
@patch("app.organization_members.service.organization_repository.get_organization_by_id")
def test_tc_03_create_member_user_not_found(mock_get_org, mock_get_user):
    """
    Verify exception when user does not exist.
    """

    organization = MagicMock(id=uuid.uuid4())

    payload = OrganizationMemberCreate(
        organization_id=organization.id,
        user_id=uuid.uuid4(),
        role_id=uuid.uuid4(),
    )

    mock_db = MagicMock()
    mock_get_org.return_value = organization
    mock_get_user.return_value = None

    with pytest.raises(UserNotFoundException):
        create_member_service(
            mock_db,
            payload,
        )


@patch("app.organization_members.service.rbac_repository.get_role_by_id")
@patch("app.organization_members.service.user_service.get_user_by_id")
@patch("app.organization_members.service.organization_repository.get_organization_by_id")
def test_tc_04_create_member_role_not_found(mock_get_org, mock_get_user, mock_get_role):
    """
    Verify exception when role does not exist.
    """

    organization = MagicMock(id=uuid.uuid4())
    user = MagicMock(id=uuid.uuid4())

    payload = OrganizationMemberCreate(
        organization_id=organization.id,
        user_id=user.id,
        role_id=uuid.uuid4(),
    )

    mock_db = MagicMock()
    mock_get_org.return_value = organization
    mock_get_user.return_value = user
    mock_get_role.return_value = None

    with pytest.raises(RoleNotFoundException):
        create_member_service(
            mock_db,
            payload,
        )


@patch("app.organization_members.service.repository.get_member_by_user_and_organization")
@patch("app.organization_members.service.rbac_repository.get_role_by_id")
@patch("app.organization_members.service.user_service.get_user_by_id")
@patch("app.organization_members.service.organization_repository.get_organization_by_id")
def test_tc_05_create_member_duplicate_member(
    mock_get_org,
    mock_get_user,
    mock_get_role,
    mock_get_member,
):
    """
    Verify duplicate member cannot be created.
    """

    organization = MagicMock(id=uuid.uuid4())
    user = MagicMock(id=uuid.uuid4())
    role = MagicMock(id=uuid.uuid4(), name="member", requires_batch=None)

    payload = OrganizationMemberCreate(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    mock_db = MagicMock()

    mock_get_org.return_value = organization
    mock_get_user.return_value = user
    mock_get_role.return_value = role
    mock_get_member.return_value = MagicMock()

    with pytest.raises(OrganizationMemberAlreadyExistsException):
        create_member_service(
            mock_db,
            payload,
        )


# ==========================================================
# Get Member Tests
# ==========================================================


@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_06_get_member_success(mock_get_member):
    """
    Verify member is returned successfully.
    """

    member = OrganizationMember(
        id=uuid.uuid4(),
    )

    mock_db = MagicMock()
    mock_get_member.return_value = member

    result = get_member_service(
        mock_db,
        member.id,
    )

    mock_get_member.assert_called_once_with(
        mock_db,
        member.id,
    )

    assert result == member


@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_07_get_member_not_found(mock_get_member):
    """
    Verify exception when member does not exist.
    """

    member_id = uuid.uuid4()

    mock_db = MagicMock()
    mock_get_member.return_value = None

    with pytest.raises(OrganizationMemberNotFoundException):
        get_member_service(
            mock_db,
            member_id,
        )


# ==========================================================
# List Members Tests
# ==========================================================


@patch("app.organization_members.service.repository.count_members")
@patch("app.organization_members.service.repository.get_members")
def test_tc_08_list_members_success(mock_get_members, mock_count_members):
    """
    Verify members are returned successfully.
    """

    mock_db = MagicMock()

    members = [
        OrganizationMember(id=uuid.uuid4()),
        OrganizationMember(id=uuid.uuid4()),
    ]

    mock_get_members.return_value = members
    mock_count_members.return_value = 2

    result = list_members_service(
        mock_db,
        page=1,
        size=10,
    )

    assert result["data"] == members
    assert result["pagination"]["total"] == 2
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["size"] == 10


@patch("app.organization_members.service.repository.count_members")
@patch("app.organization_members.service.repository.get_members")
def test_tc_09_list_members_empty(mock_get_members, mock_count_members):
    """
    Verify empty member list.
    """

    mock_db = MagicMock()

    mock_get_members.return_value = []
    mock_count_members.return_value = 0

    result = list_members_service(
        mock_db,
        page=1,
        size=10,
    )

    assert result["data"] == []
    assert result["pagination"]["total"] == 0


# ==========================================================
# Update Member Tests
# ==========================================================


@patch("app.organization_members.service.repository.update_member")
@patch("app.organization_members.service.rbac_repository.get_role_by_id")
@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_10_update_member_success(
    mock_get_member,
    mock_get_role,
    mock_update_member,
):
    """
    Verify member is updated successfully.
    """

    member = OrganizationMember(
        id=uuid.uuid4(),
        role_id=uuid.uuid4(),
    )

    new_role = uuid.uuid4()

    payload = OrganizationMemberUpdate(
        role_id=new_role,
    )

    mock_db = MagicMock()

    mock_get_member.return_value = member
    mock_get_role.return_value = MagicMock(id=new_role, name="member", requires_batch=None)
    mock_update_member.return_value = member

    update_member_service(
        mock_db,
        member.id,
        payload,
    )

    mock_update_member.assert_called_once()


@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_11_update_member_not_found(mock_get_member):
    """
    Verify exception when member is missing.
    """

    payload = OrganizationMemberUpdate()

    mock_db = MagicMock()
    mock_get_member.return_value = None

    with pytest.raises(OrganizationMemberNotFoundException):
        update_member_service(
            mock_db,
            uuid.uuid4(),
            payload,
        )


@patch("app.organization_members.service.rbac_repository.get_role_by_id")
@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_12_update_member_invalid_role(mock_get_member, mock_get_role):
    """
    Verify exception when role does not exist.
    """

    member = OrganizationMember(
        id=uuid.uuid4(),
    )

    payload = OrganizationMemberUpdate(
        role_id=uuid.uuid4(),
    )

    mock_db = MagicMock()
    mock_get_member.return_value = member
    mock_get_role.return_value = None

    with pytest.raises(RoleNotFoundException):
        update_member_service(
            mock_db,
            member.id,
            payload,
        )


# ==========================================================
# Delete Member Tests
# ==========================================================


@patch("app.organization_members.service.repository.delete_member")
@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_13_delete_member_success(mock_get_member, mock_delete_member):
    """
    Verify member is deleted successfully.
    """

    member = OrganizationMember(
        id=uuid.uuid4(),
        is_active=True,
        is_deleted=False,
    )

    mock_db = MagicMock()

    mock_get_member.return_value = member
    mock_delete_member.return_value = member

    result = delete_member_service(
        mock_db,
        member.id,
    )

    mock_delete_member.assert_called_once_with(
        mock_db,
        member,
    )

    assert result == member


@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_14_delete_member_not_found(mock_get_member):
    """
    Verify exception when deleting a non-existing member.
    """

    mock_db = MagicMock()
    mock_get_member.return_value = None

    with pytest.raises(OrganizationMemberNotFoundException):
        delete_member_service(
            mock_db,
            uuid.uuid4(),
        )


@patch("app.organization_members.service.repository.delete_member")
@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_15_delete_member_repository_called_once(mock_get_member, mock_delete_member):
    """
    Verify repository delete function is invoked exactly once.
    """

    member = OrganizationMember(
        id=uuid.uuid4(),
    )

    mock_db = MagicMock()

    mock_get_member.return_value = member
    mock_delete_member.return_value = member

    delete_member_service(
        mock_db,
        member.id,
    )

    mock_delete_member.assert_called_once()


@patch("app.organization_members.service.repository.delete_member")
@patch("app.organization_members.service.repository.get_member_by_id")
def test_tc_16_delete_member_returns_deleted_member(mock_get_member, mock_delete_member):
    """
    Verify deleted member object is returned.
    """

    member = OrganizationMember(
        id=uuid.uuid4(),
        is_active=False,
        is_deleted=True,
    )

    mock_db = MagicMock()

    mock_get_member.return_value = member
    mock_delete_member.return_value = member

    result = delete_member_service(
        mock_db,
        member.id,
    )

    assert result.is_deleted is True
    assert result.is_active is False
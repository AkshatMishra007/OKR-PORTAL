import pytest
from unittest.mock import MagicMock, patch

from app.common.exceptions import (
    OrganizationAlreadyExistsException,
    OrganizationNotFoundException,
)

from app.organizations.models import Organization

from app.organizations.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
)

from app.organizations.service import (
    create_organization_service,
    list_organizations_service,
    get_organization_service,
    update_organization_service,
    delete_organization_service,
)


# ==========================================================
# Create Organization Test Cases
# ==========================================================


@patch("app.organizations.service.repository")
def test_tc_01_create_organization_success(mock_repository):
    """
    Verify organization is created successfully
    when organization name is unique.
    """

    db = MagicMock()

    organization_data = OrganizationCreate(
        name="OpenAI",
        description="AI Research Organization",
        logo="logo.png",
        website="https://openai.com",
        email="contact@openai.com",
        phone="9999999999",
        address="USA",
    )

    mock_repository.get_organization_by_name.return_value = None

    expected_organization = Organization(
        id=1,
        name="OpenAI",
    )

    mock_repository.create_organization.return_value = (
        expected_organization
    )

    result = create_organization_service(
        db,
        organization_data,
        current_user_id=1,
    )

    assert result == expected_organization

    mock_repository.get_organization_by_name.assert_called_once_with(
        db,
        "OpenAI",
    )

    mock_repository.create_organization.assert_called_once()


@patch("app.organizations.service.repository")
def test_tc_02_create_organization_duplicate_name(mock_repository):
    """
    Verify exception is raised when organization name already exists.
    """

    db = MagicMock()

    organization_data = OrganizationCreate(
        name="OpenAI",
    )

    mock_repository.get_organization_by_name.return_value = Organization(
        id=1,
        name="OpenAI",
    )

    with pytest.raises(
        OrganizationAlreadyExistsException,
        match="Organization name already exists",
    ):
        create_organization_service(
            db,
            organization_data,
        )

    mock_repository.get_organization_by_name.assert_called_once_with(
        db,
        "OpenAI",
    )

    mock_repository.create_organization.assert_not_called()


@patch("app.organizations.service.repository")
def test_tc_04_create_organization_without_website(mock_repository):
    """
    Verify organization creation works when website is not provided.
    """

    db = MagicMock()

    organization_data = OrganizationCreate(
        name="OpenAI",
        website=None,
    )

    mock_repository.get_organization_by_name.return_value = None

    mock_repository.create_organization.return_value = Organization(
        id=1,
        name="OpenAI",
    )

    create_organization_service(
        db,
        organization_data,
    )

    created_organization = (
        mock_repository.create_organization.call_args.args[1]
    )

    assert created_organization.website is None

    mock_repository.create_organization.assert_called_once()


# ==========================================================
# Additional Create Organization Test Cases
# ==========================================================


@patch("app.organizations.service.repository")
def test_tc_05_create_organization_with_current_user_id(mock_repository):
    """
    Verify created_by is assigned from current_user_id.
    """

    db = MagicMock()

    organization_data = OrganizationCreate(
        name="Google",
    )

    mock_repository.get_organization_by_name.return_value = None

    mock_repository.create_organization.return_value = Organization(
        id=1,
        name="Google",
    )

    create_organization_service(
        db,
        organization_data,
        current_user_id=100,
    )

    created_org = (
        mock_repository.create_organization.call_args.args[1]
    )

    assert created_org.created_by == 100



@patch("app.organizations.service.repository")
def test_tc_06_create_organization_without_current_user_id(mock_repository):
    """
    Verify organization can be created without current user.
    """

    db = MagicMock()

    organization_data = OrganizationCreate(
        name="Microsoft",
    )

    mock_repository.get_organization_by_name.return_value = None

    mock_repository.create_organization.return_value = Organization(
        id=1
    )

    create_organization_service(
        db,
        organization_data,
    )

    created_org = (
        mock_repository.create_organization.call_args.args[1]
    )

    assert created_org.created_by is None


# ==========================================================
# Additional List Organization Test Cases
# ==========================================================


@patch("app.organizations.service.repository")
def test_tc_07_list_organizations_default_pagination(mock_repository):
    """
    Verify default pagination values are applied.
    """

    db = MagicMock()

    mock_repository.get_organizations.return_value = []
    mock_repository.count_organizations.return_value = 0

    result = list_organizations_service(db)

    assert result["pagination"]["page"] == 1
    assert result["pagination"]["size"] == 20

    mock_repository.get_organizations.assert_called_once_with(
        db,
        skip=0,
        limit=20,
        search=None,
        is_active=None,
    )



@patch("app.organizations.service.repository")
def test_tc_08_list_organizations_with_search(mock_repository):
    """
    Verify search parameter is passed correctly.
    """

    db = MagicMock()

    mock_repository.get_organizations.return_value = []
    mock_repository.count_organizations.return_value = 5

    result = list_organizations_service(
        db,
        search="open",
    )

    assert result["pagination"]["total"] == 5

    mock_repository.get_organizations.assert_called_once_with(
        db,
        skip=0,
        limit=20,
        search="open",
        is_active=None,
    )

# ==========================================================
# Additional Get Organization Test Cases
# ==========================================================


@patch("app.organizations.service.repository")
def test_tc_09_get_organization_repository_called(mock_repository):
    """
    Verify repository is called with correct organization id.
    """

    db = MagicMock()

    organization = Organization(
        id=10,
    )

    mock_repository.get_organization_by_id.return_value = organization

    result = get_organization_service(
        db,
        10,
    )

    assert result.id == 10

    mock_repository.get_organization_by_id.assert_called_once_with(
        db,
        10,
    )


# ==========================================================
# Additional Update Organization Test Cases
# ==========================================================


@patch("app.organizations.service.repository")
def test_tc_10_update_organization_email(mock_repository):
    """
    Verify email can be updated.
    """

    db = MagicMock()

    organization = Organization(
        id=1,
        email="old@test.com",
    )

    mock_repository.get_organization_by_id.return_value = organization
    mock_repository.update_organization.return_value = organization


    update_data = OrganizationUpdate(
        email="new@test.com",
    )

    update_organization_service(
        db,
        1,
        update_data,
    )

    assert organization.email == "new@test.com"



@patch("app.organizations.service.repository")
def test_tc_11_update_organization_status(mock_repository):
    """
    Verify active status can be updated.
    """

    db = MagicMock()

    organization = Organization(
        id=1,
        is_active=True,
    )

    mock_repository.get_organization_by_id.return_value = organization
    mock_repository.update_organization.return_value = organization


    update_data = OrganizationUpdate(
        is_active=False,
    )

    update_organization_service(
        db,
        1,
        update_data,
    )

    assert organization.is_active is False



@patch("app.organizations.service.repository")
def test_tc_12_update_organization_updated_by(mock_repository):
    """
    Verify updated_by is assigned.
    """

    db = MagicMock()

    organization = Organization(
        id=1,
    )

    mock_repository.get_organization_by_id.return_value = organization
    mock_repository.update_organization.return_value = organization


    update_organization_service(
        db,
        1,
        OrganizationUpdate(
            description="Updated",
        ),
        current_user_id=50,
    )


    assert organization.updated_by == 50

# ==========================================================
# Additional Delete Organization Test Cases
# ==========================================================


@patch("app.organizations.service.repository")
def test_tc_13_delete_organization_sets_deleted_flag(mock_repository):
    """
    Verify soft delete flags are updated correctly.
    """

    db = MagicMock()

    organization = Organization(
        id=1,
        is_active=True,
        is_deleted=False,
    )

    mock_repository.get_organization_by_id.return_value = organization
    mock_repository.delete_organization.return_value = organization


    delete_organization_service(
        db,
        1,
    )


    assert organization.is_deleted is True
    assert organization.is_active is False
    assert organization.deleted_at is not None



@patch("app.organizations.service.repository")
def test_tc_14_delete_organization_updates_user(mock_repository):
    """
    Verify deleted organization stores updated_by user.
    """

    db = MagicMock()

    organization = Organization(
        id=1,
    )

    mock_repository.get_organization_by_id.return_value = organization
    mock_repository.delete_organization.return_value = organization


    delete_organization_service(
        db,
        1,
        current_user_id=99,
    )


    assert organization.updated_by == 99


@patch("app.organizations.service.repository")
def test_tc_17_get_organization_not_found(mock_repository):
    """
    Verify OrganizationNotFoundException when organization does not exist.
    """

    db = MagicMock()
    mock_repository.get_organization_by_id.return_value = None

    with pytest.raises(
        OrganizationNotFoundException,
        match="Organization not found",
    ):
        get_organization_service(db, 999)


@patch("app.organizations.service.repository")
def test_tc_18_update_organization_not_found(mock_repository):
    """
    Verify OrganizationNotFoundException when updating a non-existent organization.
    """

    db = MagicMock()
    mock_repository.get_organization_by_id.return_value = None

    with pytest.raises(
        OrganizationNotFoundException,
        match="Organization not found",
    ):
        update_organization_service(
            db,
            999,
            OrganizationUpdate(name="New Name"),
        )


@patch("app.organizations.service.repository")
def test_tc_19_update_organization_duplicate_name_other_org(mock_repository):
    """
    Verify OrganizationAlreadyExistsException when updating name to one used by another org.
    """

    db = MagicMock()
    existing_org = Organization(id=1, name="Original Name")
    other_org = Organization(id=2, name="Taken Name")

    mock_repository.get_organization_by_id.return_value = existing_org
    mock_repository.get_organization_by_name.return_value = other_org

    with pytest.raises(
        OrganizationAlreadyExistsException,
        match="Organization name already exists",
    ):
        update_organization_service(
            db,
            1,
            OrganizationUpdate(name="Taken Name"),
        )


@patch("app.organizations.service.repository")
def test_tc_20_update_organization_optional_fields(mock_repository):
    """
    Verify updating logo, website, phone, and address fields.
    """

    db = MagicMock()
    organization = Organization(id=1)

    mock_repository.get_organization_by_id.return_value = organization
    mock_repository.update_organization.return_value = organization

    update_data = OrganizationUpdate(
        logo="new_logo.png",
        website="https://newsite.com",
        phone="1234567890",
        address="123 New St",
    )

    update_organization_service(
        db,
        1,
        update_data,
    )

    assert organization.logo == "new_logo.png"
    assert str(organization.website) == "https://newsite.com/"
    assert organization.phone == "1234567890"
    assert organization.address == "123 New St"


@patch("app.organizations.service.repository")
def test_tc_21_delete_organization_not_found(mock_repository):
    """
    Verify OrganizationNotFoundException when deleting a non-existent organization.
    """

    db = MagicMock()
    mock_repository.get_organization_by_id.return_value = None

    with pytest.raises(
        OrganizationNotFoundException,
        match="Organization not found",
    ):
        delete_organization_service(db, 999)
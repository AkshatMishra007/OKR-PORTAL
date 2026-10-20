import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import (
    RoleAlreadyExistsException,
    RoleNotFoundException,
)

from app.rbac.schemas import (
    RoleCreate,
    RoleUpdate,
)

from app.rbac.service import (
    create_role_service,
    get_role_service,
    list_roles_service,
    update_role_service,
    delete_role_service,
)

@patch("app.rbac.service.create_role")
@patch("app.rbac.service.get_role_by_name")
def test_tc_01_create_role_success(
    mock_get_name,
    mock_create_role,
):

    db = MagicMock()

    role_data = RoleCreate(
        name="Admin",
        description="Administrator",
    )

    mock_get_name.return_value = None

    expected_role = {
        "name": "Admin",
    }

    mock_create_role.return_value = expected_role


    result = create_role_service(
        db,
        role_data,
    )


    assert result == expected_role


    mock_get_name.assert_called_once_with(
        db,
        "Admin",
    )

    mock_create_role.assert_called_once_with(
        db,
        role_data,
    )


@patch("app.rbac.service.get_role_by_name")
def test_tc_02_create_role_duplicate_name(
    mock_get_name,
):

    db = MagicMock()


    role_data = RoleCreate(
        name="Admin",
    )


    mock_get_name.return_value = MagicMock()


    with pytest.raises(
        RoleAlreadyExistsException,
        match="Role name already exists.",
    ):

        create_role_service(
            db,
            role_data,
        )


@patch("app.rbac.service.get_role_by_id")
def test_tc_04_get_role_success(
    mock_get_role,
):

    db = MagicMock()

    role_id = uuid.uuid4()

    role = MagicMock(
        id=role_id,
        name="Admin",
    )


    mock_get_role.return_value = role


    result = get_role_service(
        db,
        role_id,
    )


    assert result == role


    mock_get_role.assert_called_once_with(
        db,
        role_id,
    )


@patch("app.rbac.service.get_role_by_id")
def test_tc_05_get_role_not_found(
    mock_get_role,
):

    db = MagicMock()

    role_id = uuid.uuid4()


    mock_get_role.return_value = None


    with pytest.raises(
        RoleNotFoundException,
        match="Role not found.",
    ):

        get_role_service(
            db,
            role_id,
        )

@patch("app.rbac.service.list_roles")
def test_tc_06_list_roles_success(
    mock_list_roles,
):

    db = MagicMock()


    expected_result = (
        [
            {
                "name": "Admin",
            }
        ],
        1,
    )


    mock_list_roles.return_value = expected_result


    result = list_roles_service(
        db,
        page=1,
        size=10,
        search=None,
    )


    assert result == expected_result


    mock_list_roles.assert_called_once_with(
        db,
        1,
        10,
        None,
    )

@patch("app.rbac.service.list_roles")
def test_tc_07_list_roles_with_search(
    mock_list_roles,
):

    db = MagicMock()


    mock_list_roles.return_value = (
        [],
        0,
    )


    result = list_roles_service(
        db,
        page=1,
        size=20,
        search="admin",
    )


    assert result == (
        [],
        0,
    )


    mock_list_roles.assert_called_once_with(
        db,
        1,
        20,
        "admin",
    )

@patch("app.rbac.service.update_role")
@patch("app.rbac.service.get_role_by_name")
@patch("app.rbac.service.get_role_by_id")
def test_tc_08_update_role_success(
    mock_get_role,
    mock_get_role_by_name,
    mock_update_role,
):

    db = MagicMock()

    role_id = uuid.uuid4()

    role = MagicMock(
        id=role_id,
        name="User",
    )

    update_data = RoleUpdate(
        name="Manager",
    )

    mock_get_role.return_value = role

    # Important: simulate no duplicate role name
    mock_get_role_by_name.return_value = None

    mock_update_role.return_value = role


    result = update_role_service(
        db,
        role_id,
        update_data,
    )


    assert result == role

    mock_get_role.assert_called_once_with(
        db,
        role_id,
    )

    mock_update_role.assert_called_once()

@patch("app.rbac.service.get_role_by_id")
def test_tc_09_update_role_not_found(
    mock_get_role,
):

    db = MagicMock()

    role_id = uuid.uuid4()


    mock_get_role.return_value = None


    with pytest.raises(
        RoleNotFoundException,
        match="Role not found.",
    ):

        update_role_service(
            db,
            role_id,
            RoleUpdate(
                name="Admin",
            ),
        )

@patch("app.rbac.service.get_role_by_name")
@patch("app.rbac.service.get_role_by_id")
def test_tc_10_update_role_duplicate_name(
    mock_get_role,
    mock_get_name,
):

    db = MagicMock()

    role_id = uuid.uuid4()


    role = MagicMock(
        id=role_id,
        name="User",
    )


    mock_get_role.return_value = role

    mock_get_name.return_value = MagicMock()


    with pytest.raises(
        RoleAlreadyExistsException,
        match="Role name already exists.",
    ):

        update_role_service(
            db,
            role_id,
            RoleUpdate(
                name="Admin",
            ),
        )

@patch("app.rbac.service.delete_role")
@patch("app.rbac.service.get_role_by_id")
def test_tc_11_delete_role_success(
    mock_get_role,
    mock_delete_role,
):

    db = MagicMock()

    role_id = uuid.uuid4()


    role = MagicMock(
        id=role_id,
    )


    mock_get_role.return_value = role


    result = delete_role_service(
        db,
        role_id,
    )


    assert result is True


    mock_delete_role.assert_called_once_with(
        db,
        role,
    )

@patch("app.rbac.service.get_role_by_id")
def test_tc_12_delete_role_not_found(
    mock_get_role,
):

    db = MagicMock()

    role_id = uuid.uuid4()


    mock_get_role.return_value = None


    with pytest.raises(
        RoleNotFoundException,
        match="Role not found.",
    ):

        delete_role_service(
            db,
            role_id,
        )


@patch("app.rbac.service.update_role")
@patch("app.rbac.service.get_role_by_name")
@patch("app.rbac.service.get_role_by_id")
def test_tc_13_update_role_same_name_bypasses_duplicate_check(
    mock_get_role,
    mock_get_name,
    mock_update_role,
):
    """
    Verify that updating a role with its current name bypasses get_role_by_name check.
    """

    db = MagicMock()
    role_id = uuid.uuid4()

    role = MagicMock(id=role_id)
    role.name = "Admin"

    mock_get_role.return_value = role
    mock_get_name.return_value = role
    mock_update_role.return_value = role

    update_data = RoleUpdate(
        name="Admin",
        description="Updated Admin description",
    )

    result = update_role_service(
        db,
        role_id,
        update_data,
    )

    assert result == role
    mock_update_role.assert_called_once_with(db, role, update_data)
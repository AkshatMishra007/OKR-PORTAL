import uuid

from app.rbac.models import Role
from app.rbac.repository import (
    create_role,
    get_role_by_id,
    get_role_by_name,
    list_roles,
    update_role,
    delete_role,
)

from app.rbac.schemas import (
    RoleCreate,
    RoleUpdate,
)


# ==========================================================
# Create Role Tests
# ==========================================================


def test_tc_01_create_role_success(db_session):
    """
    Verify role is created successfully.
    """

    role_data = RoleCreate(
        name="Admin",
        description="Administrator role",
    )

    result = create_role(
        db_session,
        role_data,
    )

    assert result.id is not None
    assert result.name == "Admin"
    assert result.description == "Administrator role"

    db_session.close()



# ==========================================================
# Get Role By ID Tests
# ==========================================================


def test_tc_02_get_role_by_id_success(db_session):

    role = Role(
        name="Manager",
        description="Manager role",
        is_active=True,
        is_deleted=False,
    )

    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    result = get_role_by_id(
        db_session,
        role.id,
    )

    assert result is not None
    assert result.id == role.id
    assert result.name == "Manager"



def test_tc_03_get_role_by_id_deleted_role(db_session):

    role = Role(
        name="Deleted",
        is_active=False,
        is_deleted=True,
    )

    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    result = get_role_by_id(
        db_session,
        role.id,
    )

    assert result is None



# ==========================================================
# Get Role By Name Tests
# ==========================================================


def test_tc_04_get_role_by_name_success(db_session):

    role = Role(
        name="Developer",
        is_deleted=False,
    )

    db_session.add(role)
    db_session.commit()

    result = get_role_by_name(
        db_session,
        "Developer",
    )

    assert result is not None
    assert result.name == "Developer"



def test_tc_05_get_role_by_name_deleted_role(db_session):

    role = Role(
        name="OldRole",
        is_deleted=True,
    )

    db_session.add(role)
    db_session.commit()

    result = get_role_by_name(
        db_session,
        "OldRole",
    )

    assert result is None



# ==========================================================
# List Roles Tests
# ==========================================================


def test_tc_08_list_roles_without_search(db_session):

    role1 = Role(
        name="Admin",
        is_deleted=False,
    )

    role2 = Role(
        name="User",
        is_deleted=False,
    )

    db_session.add_all(
        [
            role1,
            role2,
        ]
    )

    db_session.commit()

    roles, total = list_roles(
        db_session,
        page=1,
        size=10,
    )

    assert total == 2
    assert len(roles) == 2



def test_tc_09_list_roles_with_search(db_session):

    role1 = Role(
        name="Administrator",
        is_deleted=False,
    )

    role2 = Role(
        name="Employee",
        is_deleted=False,
    )

    db_session.add_all(
        [
            role1,
            role2,
        ]
    )

    db_session.commit()

    roles, total = list_roles(
        db_session,
        page=1,
        size=10,
        search="Admin",
    )

    assert total == 1
    assert roles[0].name == "Administrator"



def test_tc_10_list_roles_pagination(db_session):

    for index in range(5):

        db_session.add(
            Role(
                name=f"Role {index}",
                is_deleted=False,
            )
        )

    db_session.commit()

    roles, total = list_roles(
        db_session,
        page=2,
        size=2,
    )

    assert total == 5
    assert len(roles) == 2



# ==========================================================
# Update Role Tests
# ==========================================================


def test_tc_11_update_role_success(db_session):

    role = Role(
        name="Old Name",
        description="Old description",
    )

    db_session.add(role)
    db_session.commit()

    update_data = RoleUpdate(
        name="New Name",
        description="New description",
    )

    result = update_role(
        db_session,
        role,
        update_data,
    )

    assert result.name == "New Name"
    assert result.description == "New description"



def test_tc_12_update_role_partial_update(db_session):

    role = Role(
        name="Admin",
        description="Old",
    )

    db_session.add(role)
    db_session.commit()

    update_data = RoleUpdate(
        description="Updated",
    )

    result = update_role(
        db_session,
        role,
        update_data,
    )

    assert result.name == "Admin"
    assert result.description == "Updated"



# ==========================================================
# Delete Role Tests
# ==========================================================


def test_tc_13_delete_role_success(db_session):

    role = Role(
        name="Delete Test",
        is_active=True,
        is_deleted=False,
    )

    db_session.add(role)
    db_session.commit()

    delete_role(
        db_session,
        role,
    )

    db_session.refresh(role)

    assert role.is_active is False
    assert role.is_deleted is True
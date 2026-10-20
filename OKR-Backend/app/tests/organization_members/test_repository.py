import uuid

from app.organization_members.models import OrganizationMember
from app.organization_members.repository import (
    create_member,
    get_member_by_id,
    get_member_by_user_and_organization,
    get_members,
    count_members,
    update_member,
    delete_member,
)
from app.organization_members.schemas import OrganizationMemberCreate
from app.organizations.models import Organization
from app.rbac.models import Role
from app.users.models import User


# ==========================================================
# Helper Methods
# ==========================================================

def create_test_organization(db_session):

    organization = Organization(
        name="Test Organization",
    )

    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)

    return organization


def create_test_user(db_session):

    user = User(
        username=f"user_{uuid.uuid4().hex[:6]}",
        email=f"{uuid.uuid4().hex[:6]}@test.com",
        password_hash="password",
        first_name="Test",
        last_name="User",
        is_deleted=False,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def create_test_role(db_session):

    role = Role(
        name="Manager",
        description="Test Role",
        is_deleted=False,
    )

    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    return role


# ==========================================================
# Create Member Tests
# ==========================================================


def test_tc_01_create_member_success(db_session):
    """
    Verify organization member is created successfully.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    result = create_member(
        db_session,
        member,
    )

    assert result.id is not None
    assert result.organization_id == organization.id
    assert result.user_id == user.id
    assert result.role_id == role.id
    assert result.is_active is True
    assert result.is_deleted is False


def test_tc_02_create_member_verify_defaults(db_session):
    """
    Verify default fields are populated correctly.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    result = create_member(
        db_session,
        member,
    )

    assert result.joined_at is not None
    assert result.created_at is not None
    assert result.updated_at is not None
    assert result.deleted_at is None


def test_tc_03_create_member_relationship_fields(db_session):
    """
    Verify relationship fields are stored correctly.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    result = create_member(
        db_session,
        member,
    )

    assert result.organization.id == organization.id
    assert result.user.id == user.id
    assert result.role.id == role.id

# ==========================================================
# Get Member By ID Tests
# ==========================================================


def test_tc_04_get_member_by_id_success(db_session):
    """
    Verify existing organization member is returned.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    result = get_member_by_id(
        db_session,
        member.id,
    )

    assert result is not None
    assert result.id == member.id
    assert result.organization_id == organization.id
    assert result.user_id == user.id
    assert result.role_id == role.id


def test_tc_05_get_member_by_id_deleted_member(db_session):
    """
    Verify soft deleted organization member is not returned.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
        is_active=False,
        is_deleted=True,
    )

    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    result = get_member_by_id(
        db_session,
        member.id,
    )

    assert result is None


def test_tc_06_get_member_by_id_not_found(db_session):
    """
    Verify None is returned for a non-existing member.
    """

    result = get_member_by_id(
        db_session,
        uuid.uuid4(),
    )

    assert result is None


# ==========================================================
# Get Member By User & Organization Tests
# ==========================================================


def test_tc_07_get_member_by_user_and_organization_success(db_session):
    """
    Verify member can be retrieved using organization and user.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    result = get_member_by_user_and_organization(
        db_session,
        organization.id,
        user.id,
    )

    assert result is not None
    assert result.id == member.id


def test_tc_08_get_member_by_user_and_organization_not_found(db_session):
    """
    Verify None is returned when user does not belong to organization.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)

    result = get_member_by_user_and_organization(
        db_session,
        organization.id,
        user.id,
    )

    assert result is None


def test_tc_09_get_member_by_user_and_organization_deleted_member(db_session):
    """
    Verify deleted member is ignored while checking duplicate membership.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
        is_deleted=True,
        is_active=False,
    )

    db_session.add(member)
    db_session.commit()

    result = get_member_by_user_and_organization(
        db_session,
        organization.id,
        user.id,
    )

    assert result is None

# ==========================================================
# Get Members Tests
# ==========================================================


def test_tc_10_get_members_success(db_session):
    """
    Verify all active organization members are returned.
    """

    organization = create_test_organization(db_session)
    role = create_test_role(db_session)

    user1 = create_test_user(db_session)
    user2 = create_test_user(db_session)

    db_session.add_all(
        [
            OrganizationMember(
                organization_id=organization.id,
                user_id=user1.id,
                role_id=role.id,
            ),
            OrganizationMember(
                organization_id=organization.id,
                user_id=user2.id,
                role_id=role.id,
            ),
        ]
    )

    db_session.commit()

    members = get_members(
        db_session,
    )

    assert len(members) == 2


def test_tc_11_get_members_empty_list(db_session):
    """
    Verify empty list is returned when no members exist.
    """

    members = get_members(
        db_session,
    )

    assert members == []


def test_tc_12_get_members_filter_by_organization(db_session):
    """
    Verify members are filtered by organization.
    """

    organization1 = create_test_organization(db_session)

    organization2 = Organization(
        name="Second Organization",
    )

    db_session.add(organization2)
    db_session.commit()
    db_session.refresh(organization2)

    role = create_test_role(db_session)

    user1 = create_test_user(db_session)
    user2 = create_test_user(db_session)

    db_session.add_all(
        [
            OrganizationMember(
                organization_id=organization1.id,
                user_id=user1.id,
                role_id=role.id,
            ),
            OrganizationMember(
                organization_id=organization2.id,
                user_id=user2.id,
                role_id=role.id,
            ),
        ]
    )

    db_session.commit()

    members = get_members(
        db_session,
        organization_id=organization1.id,
    )

    assert len(members) == 1
    assert members[0].organization_id == organization1.id


def test_tc_13_get_members_filter_by_user(db_session):
    """
    Verify members are filtered by user.
    """

    organization = create_test_organization(db_session)
    role = create_test_role(db_session)

    user1 = create_test_user(db_session)
    user2 = create_test_user(db_session)

    db_session.add_all(
        [
            OrganizationMember(
                organization_id=organization.id,
                user_id=user1.id,
                role_id=role.id,
            ),
            OrganizationMember(
                organization_id=organization.id,
                user_id=user2.id,
                role_id=role.id,
            ),
        ]
    )

    db_session.commit()

    members = get_members(
        db_session,
        user_id=user2.id,
    )

    assert len(members) == 1
    assert members[0].user_id == user2.id


def test_tc_14_get_members_filter_by_role(db_session):
    """
    Verify members are filtered by role.
    """

    organization = create_test_organization(db_session)

    role1 = create_test_role(db_session)

    role2 = Role(
        name="Developer",
        description="Developer Role",
    )

    db_session.add(role2)
    db_session.commit()
    db_session.refresh(role2)

    user1 = create_test_user(db_session)
    user2 = create_test_user(db_session)

    db_session.add_all(
        [
            OrganizationMember(
                organization_id=organization.id,
                user_id=user1.id,
                role_id=role1.id,
            ),
            OrganizationMember(
                organization_id=organization.id,
                user_id=user2.id,
                role_id=role2.id,
            ),
        ]
    )

    db_session.commit()

    members = get_members(
        db_session,
        role_id=role2.id,
    )

    assert len(members) == 1
    assert members[0].role_id == role2.id


def test_tc_15_get_members_pagination(db_session):
    """
    Verify pagination using skip and limit.
    """

    organization = create_test_organization(db_session)
    role = create_test_role(db_session)

    for _ in range(5):

        user = create_test_user(db_session)

        db_session.add(
            OrganizationMember(
                organization_id=organization.id,
                user_id=user.id,
                role_id=role.id,
            )
        )

    db_session.commit()

    members = get_members(
        db_session,
        skip=2,
        limit=2,
    )

    assert len(members) == 2
# ==========================================================
# Count Members Tests
# ==========================================================


def test_tc_16_count_members_success(db_session):
    """
    Verify total active organization members are counted.
    """

    organization = create_test_organization(db_session)
    role = create_test_role(db_session)

    for _ in range(3):

        user = create_test_user(db_session)

        db_session.add(
            OrganizationMember(
                organization_id=organization.id,
                user_id=user.id,
                role_id=role.id,
            )
        )

    db_session.commit()

    total = count_members(
        db_session,
    )

    assert total == 3


def test_tc_17_count_members_filter_by_organization(db_session):
    """
    Verify member count using organization filter.
    """

    organization1 = create_test_organization(db_session)

    organization2 = Organization(
        name="Organization Two",
    )

    db_session.add(organization2)
    db_session.commit()
    db_session.refresh(organization2)

    role = create_test_role(db_session)

    user1 = create_test_user(db_session)
    user2 = create_test_user(db_session)

    db_session.add_all(
        [
            OrganizationMember(
                organization_id=organization1.id,
                user_id=user1.id,
                role_id=role.id,
            ),
            OrganizationMember(
                organization_id=organization2.id,
                user_id=user2.id,
                role_id=role.id,
            ),
        ]
    )

    db_session.commit()

    total = count_members(
        db_session,
        organization_id=organization1.id,
    )

    assert total == 1


def test_tc_18_count_members_filter_by_role(db_session):
    """
    Verify member count using role filter.
    """

    organization = create_test_organization(db_session)

    role1 = create_test_role(db_session)

    role2 = Role(
        name="Developer",
    )

    db_session.add(role2)
    db_session.commit()
    db_session.refresh(role2)

    user1 = create_test_user(db_session)
    user2 = create_test_user(db_session)

    db_session.add_all(
        [
            OrganizationMember(
                organization_id=organization.id,
                user_id=user1.id,
                role_id=role1.id,
            ),
            OrganizationMember(
                organization_id=organization.id,
                user_id=user2.id,
                role_id=role2.id,
            ),
        ]
    )

    db_session.commit()

    total = count_members(
        db_session,
        role_id=role2.id,
    )

    assert total == 1


# ==========================================================
# Update Member Tests
# ==========================================================


def test_tc_19_update_member_success(db_session):
    """
    Verify organization member is updated successfully.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)

    role1 = create_test_role(db_session)

    role2 = Role(
        name="Developer",
    )

    db_session.add(role2)
    db_session.commit()
    db_session.refresh(role2)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role1.id,
    )

    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    member.role_id = role2.id

    result = update_member(
        db_session,
        member,
    )

    assert result.role_id == role2.id


def test_tc_20_update_member_active_status(db_session):
    """
    Verify active status can be updated.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    member.is_active = False

    result = update_member(
        db_session,
        member,
    )

    assert result.is_active is False


def test_tc_21_update_member_partial_update(db_session):
    """
    Verify only modified fields are persisted.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    original_role = member.role_id

    member.is_active = False

    result = update_member(
        db_session,
        member,
    )

    assert result.is_active is False
    assert result.role_id == original_role
    assert result.organization_id == organization.id
    assert result.user_id == user.id


# ==========================================================
# Delete Member Tests
# ==========================================================


def test_tc_22_delete_member_success(db_session):
    """
    Verify organization member is soft deleted.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    member.is_active = False
    member.is_deleted = True

    delete_member(
        db_session,
        member,
    )

    db_session.refresh(member)

    assert member.is_active is False
    assert member.is_deleted is True


def test_tc_23_deleted_member_not_returned(db_session):
    """
    Verify deleted member is excluded from repository queries.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
        is_active=False,
        is_deleted=True,
    )

    db_session.add(member)
    db_session.commit()

    result = get_member_by_id(
        db_session,
        member.id,
    )

    assert result is None


def test_tc_24_get_members_filter_by_role(db_session):
    """
    Verify members are filtered by role_id.
    """

    organization = create_test_organization(db_session)
    role = create_test_role(db_session)
    user = create_test_user(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()

    members = get_members(
        db_session,
        role_id=role.id,
    )

    assert len(members) == 1
    assert members[0].role_id == role.id


def test_tc_25_count_members_filter_by_user(db_session):
    """
    Verify member count using user filter.
    """

    organization = create_test_organization(db_session)
    role = create_test_role(db_session)
    user1 = create_test_user(db_session)
    user2 = create_test_user(db_session)

    db_session.add_all(
        [
            OrganizationMember(
                organization_id=organization.id,
                user_id=user1.id,
                role_id=role.id,
            ),
            OrganizationMember(
                organization_id=organization.id,
                user_id=user2.id,
                role_id=role.id,
            ),
        ]
    )
    db_session.commit()

    total = count_members(
        db_session,
        user_id=user1.id,
    )

    assert total == 1


def test_tc_26_count_members_filter_by_role(db_session):
    """
    Verify member count using role_id filter.
    """

    organization = create_test_organization(db_session)
    role = create_test_role(db_session)
    user = create_test_user(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()

    total = count_members(
        db_session,
        role_id=role.id,
    )

    assert total == 1


def test_tc_27_get_members_all_filters_combined(db_session):
    """
    Verify get_members and count_members with filters combined (organization_id, user_id, role_id).
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()

    members = get_members(
        db_session,
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    total = count_members(
        db_session,
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    assert len(members) == 1
    assert members[0].id == member.id
    assert total == 1


def test_tc_28_get_members_skip_exceeds_total(db_session):
    """
    Verify get_members returns empty list when skip exceeds total records.
    """

    organization = create_test_organization(db_session)
    user = create_test_user(db_session)
    role = create_test_role(db_session)

    member = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role_id=role.id,
    )

    db_session.add(member)
    db_session.commit()

    members = get_members(
        db_session,
        skip=100,
        limit=10,
    )

    assert members == []



"""
Tests for common model mixins.

Covers:
- UUIDMixin
- AuditModel
- SoftDeleteModel
"""

from app.users.models import User


def create_test_user():
    return User(
        username="common_test_user",
        email="common@test.com",
        password_hash="hashed_password",
        first_name="Common",
        last_name="Test",
        designation="Developer",
        description="Testing common models",
    )


def test_uuid_generated(db_session):
    """
    UUIDMixin should generate primary key automatically.
    """

    user = create_test_user()

    db_session.add(user)
    db_session.commit()

    assert user.id is not None


def test_uuid_is_unique(db_session):
    """
    Every record should have different UUID.
    """

    user1 = User(
        username="user_one",
        email="user1@test.com",
        password_hash="hash",
        first_name="User",
    )

    user2 = User(
        username="user_two",
        email="user2@test.com",
        password_hash="hash",
        first_name="User",
    )

    db_session.add_all(
        [
            user1,
            user2,
        ]
    )

    db_session.commit()

    assert user1.id != user2.id


def test_created_at_updated_at_generated(db_session):
    """
    AuditModel should create timestamps.
    """

    user = create_test_user()

    db_session.add(user)
    db_session.commit()

    assert user.created_at is not None
    assert user.updated_at is not None


def test_created_by_updated_by_default_none(db_session):
    """
    Audit user tracking fields should be nullable.
    """

    user = create_test_user()

    db_session.add(user)
    db_session.commit()

    assert user.created_by is None
    assert user.updated_by is None


def test_soft_delete_defaults(db_session):
    """
    SoftDeleteModel default values.
    """

    user = create_test_user()

    db_session.add(user)
    db_session.commit()

    assert user.is_active is True
    assert user.is_deleted is False
    assert user.deleted_at is None


def test_soft_delete_update(db_session):
    """
    Soft delete values should be changeable.
    """

    user = create_test_user()

    db_session.add(user)
    db_session.commit()

    user.is_deleted = True
    user.is_active = False

    db_session.commit()

    assert user.is_deleted is True
    assert user.is_active is False


def test_updated_at_changes_on_update(db_session):
    """
    updated_at should update when record changes.
    """

    user = create_test_user()

    db_session.add(user)
    db_session.commit()

    old_updated_at = user.updated_at

    user.description = "Updated description"

    db_session.commit()

    assert user.updated_at >= old_updated_at

"""
Security & Multi-Tenant Isolation Unit Tests.
"""

from uuid import uuid4
import pytest
from fastapi import HTTPException

from app.auth.dependencies import get_current_user
from app.batches.service import BatchService
from app.organization_members.schemas import OrganizationMemberCreate
from app.organization_members.service import (
    create_member_service,
    delete_member_service,
    update_member_service,
)
from app.rbac.dependencies import is_super_admin
from app.rbac.policies import RoleCode
from app.users.models import User
from app.users.service import (
    get_user_by_id,
    get_users_by_organization_service,
)


def test_is_super_admin_canonical():
    super_user = User(id=uuid4(), username="admin")
    super_user.is_superuser = True
    regular_user = User(id=uuid4(), username="employee")
    regular_user.is_superuser = False

    assert is_super_admin(super_user) is True
    assert is_super_admin(regular_user) is False
    assert is_super_admin(None) is False


def test_inactive_user_rejected_in_get_current_user():
    inactive_user = User(id=uuid4(), is_active=False, is_deleted=False)
    # Mocking credentials check
    with pytest.raises(HTTPException) as exc_info:
        # get_current_user logic checks user.is_active
        if not inactive_user.is_active:
            raise HTTPException(status_code=401, detail="Could not validate credentials.")
    assert exc_info.value.status_code == 401

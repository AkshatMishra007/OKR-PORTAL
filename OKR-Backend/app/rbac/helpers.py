from typing import Iterable

from app.rbac.policies import (
    ROLE_PERMISSIONS,
    USER_ACCESS_SCOPE,
    RoleCode,
    UserAccessScope,
)


def normalize_role_code(
    role_name: str | None,
) -> str | None:
    """
    Normalize a role name into the format used by RoleCode.

    Example:
        "org_admin" -> "ORG_ADMIN"
        "Org_Admin" -> "ORG_ADMIN"
    """
    if not role_name:
        return None

    return role_name.strip().upper().replace("-", "_").replace(" ", "_")


def get_role_code(
    role_name: str | None,
) -> RoleCode | None:
    """
    Convert a database role name into a RoleCode.
    """
    normalized = normalize_role_code(role_name)

    if not normalized:
        return None

    try:
        return RoleCode(normalized)
    except ValueError:
        return None


def get_role_permissions(
    role_code: RoleCode | str | None,
) -> list[str]:
    """
    Return all permissions assigned to a role.
    """
    if not role_code:
        return []

    if isinstance(role_code, str):
        role_code = get_role_code(role_code)

    if not role_code:
        return []

    return ROLE_PERMISSIONS.get(role_code, [])


def role_has_permission(
    role_code: RoleCode | str | None,
    permission: str,
) -> bool:
    """
    Check whether a role has a specific permission.
    """
    permissions = get_role_permissions(role_code)

    return permission in permissions


def get_user_access_scope(
    role_code: RoleCode | str | None,
) -> UserAccessScope:
    """
    Return the user-data access scope associated
    with a role.
    """
    if not role_code:
        return UserAccessScope.NONE

    if isinstance(role_code, str):
        role_code = get_role_code(role_code)

    if not role_code:
        return UserAccessScope.NONE

    return USER_ACCESS_SCOPE.get(
        role_code,
        UserAccessScope.NONE,
    )


def role_has_any_permission(
    role_code: RoleCode | str | None,
    permissions: Iterable[str],
) -> bool:
    """
    Check whether a role has at least one
    permission from the supplied permissions.
    """
    role_permissions = set(
        get_role_permissions(role_code)
    )

    return any(
        permission in role_permissions
        for permission in permissions
    )


def role_has_all_permissions(
    role_code: RoleCode | str | None,
    permissions: Iterable[str],
) -> bool:
    """
    Check whether a role has all supplied permissions.
    """
    role_permissions = set(
        get_role_permissions(role_code)
    )

    return all(
        permission in role_permissions
        for permission in permissions
    )

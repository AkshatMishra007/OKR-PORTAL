from enum import Enum


class RoleCode(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    BATCH_ADMIN = "BATCH_ADMIN"
    EMPLOYEE = "EMPLOYEE"


class UserAccessScope(str, Enum):
    """
    Defines the maximum user-data scope available to a role.
    """

    GLOBAL = "GLOBAL"
    ORGANIZATION = "ORGANIZATION"
    BATCH = "BATCH"
    SELF = "SELF"
    NONE = "NONE"


ROLE_PERMISSIONS: dict[RoleCode, list[str]] = {
    RoleCode.SUPER_ADMIN: [
        # Organization
        "organization.create",
        "organization.update",
        "organization.delete",
        "organization.view",
        "organization.manage",

        # Users
        "user.create",
        "user.update",
        "user.delete",
        "user.view",

        # Roles
        "role.create",
        "role.update",
        "role.delete",
        "role.view",

        # Batch
        "batch.create",
        "batch.update",
        "batch.delete",
        "batch.view",
        "batch.manage",
    ],

    RoleCode.ORG_ADMIN: [
        # Organization
        "organization.view",

        # Users
        "user.create",
        "user.update",
        "user.view",

        # Batch
        "batch.create",
        "batch.update",
        "batch.delete",
        "batch.view",
        "batch.manage",

        # OKR
        "okr.create",
        "okr.update",
        "okr.view",

        # Reports
        "report.view",
    ],

    RoleCode.BATCH_ADMIN: [
        # Users
        "user.view",

        # Batch
        "batch.view",
        "batch.update",
        "batch.manage",
        "batch.member.manage",

        # OKR
        "okr.create",
        "okr.update",
        "okr.view",

        # Weekly updates
        "weekly_update.review",

        # Tracker
        "tracker.review",

        # Reports
        "report.view",
    ],

    RoleCode.EMPLOYEE: [
        # No batch permissions

        # OKR
        "okr.view",
        "okr.update",

        # Weekly updates
        "weekly_update.create",

        # Tracker
        "tracker.update",
    ],
}


USER_ACCESS_SCOPE: dict[RoleCode, UserAccessScope] = {
    RoleCode.SUPER_ADMIN: UserAccessScope.GLOBAL,
    RoleCode.ORG_ADMIN: UserAccessScope.ORGANIZATION,
    RoleCode.BATCH_ADMIN: UserAccessScope.BATCH,
    RoleCode.EMPLOYEE: UserAccessScope.SELF,
}

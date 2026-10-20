export const MODULE_PERMISSIONS = {
    DASHBOARD: ["ORG_ADMIN", "SUPER_ADMIN"],

    MY_OKR: [
        "EMPLOYEE",
        "BATCH_ADMIN",
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],

    TEAM_OKR: [
        "BATCH_ADMIN",
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],

    PERFORMANCE: [
        "BATCH_ADMIN",
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],

    LEADERBOARD: [
        "EMPLOYEE",
        "BATCH_ADMIN",
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],

    RAISE_QUERY: [
        "EMPLOYEE",
        "BATCH_ADMIN",
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],

    MANAGE_QUERY: [
        "SUPER_ADMIN",
    ],

    USERS: [
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],

    BATCHES: [
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],

    // These are Super Admin-only based on
    // the "Super Admin = all modules" requirement.
    ORGANIZATIONS: [
        "SUPER_ADMIN",
    ],

    ROLES: [
        "SUPER_ADMIN",
    ],


    MANAGE_OKR: [
        "BATCH_ADMIN",
        "ORG_ADMIN",
        "SUPER_ADMIN",
    ],
};


export const hasModuleAccess = (role, module) => {
    if (!role) {
        return false;
    }

    const normalizedRole = role
        .toString()
        .trim()
        .toUpperCase()
        .replace(/\s+/g, "_");

    // Super Admin has access to every module.
    if (normalizedRole === "SUPER_ADMIN") {
        return true;
    }

    return (
        MODULE_PERMISSIONS[module]?.includes(normalizedRole) || false
    );
};
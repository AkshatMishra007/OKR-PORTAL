from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException
from app.organization_members.models import OrganizationMember
from app.queries.models import Query
from app.rbac.access import AccessScope, get_access_scope
from app.users.models import User


def require_query_access(
    db: Session,
    user: User,
    query: Query,
    write: bool = False,
) -> AccessScope:
    """
    Validate whether a user can access a query.

    Access rules:

    SUPER_ADMIN
        Can access all queries.

    ORG_ADMIN
        Can access queries raised by or assigned to
        members of their organization.

    BATCH_ADMIN
        Can access queries raised by or assigned to
        members of their assigned batches.

    EMPLOYEE
        Can access their own queries or queries assigned
        to them.

    write=True
        Restricts write operations to users with management
        privileges or users who own/are assigned the query.
    """

    scope = get_access_scope(
        db,
        user,
    )

    # ------------------------------------------------------
    # Super Admin
    # ------------------------------------------------------

    if scope.is_super_admin:
        return scope

    # ------------------------------------------------------
    # Get organization memberships for query participants
    # ------------------------------------------------------

    participant_user_ids = {
        query.user_id,
    }

    if query.assigned_to:
        participant_user_ids.add(
            query.assigned_to
        )

    memberships = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id.in_(
                participant_user_ids
            ),
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .all()
    )

    # ------------------------------------------------------
    # Determine query scope
    # ------------------------------------------------------

    query_organization_ids = {
        membership.organization_id
        for membership in memberships
    }

    from app.batches.models import BatchMember

    participant_batch_memberships = (
        db.query(BatchMember)
        .filter(
            BatchMember.user_id.in_(participant_user_ids),
            BatchMember.is_deleted.is_(False),
            BatchMember.is_active.is_(True),
        )
        .all()
    )
    query_batch_ids = {
        bm.batch_id
        for bm in participant_batch_memberships
        if bm.batch_id
    }

    is_owner = (
        query.user_id == user.id
    )

    is_assigned = (
        query.assigned_to == user.id
    )

    in_organization = bool(
        query_organization_ids
        & scope.organization_ids
    )

    in_batch = bool(
        query_batch_ids
        & scope.batch_ids
    )

    # ------------------------------------------------------
    # Role checks
    # ------------------------------------------------------

    is_org_admin = (
        "ORG_ADMIN" in scope.roles
    )

    is_batch_admin = (
        "BATCH_ADMIN" in scope.roles
    )

    is_employee = (
        "EMPLOYEE" in scope.roles
    )

    # ------------------------------------------------------
    # Read access
    # ------------------------------------------------------

    allowed = (
        (is_org_admin and in_organization)
        or (is_batch_admin and in_batch)
        or (is_employee and (is_owner or is_assigned))
    )

    if not allowed:
        raise ForbiddenException(
            "You do not have access to this query."
        )

    # ------------------------------------------------------
    # Write access
    # ------------------------------------------------------

    if write:
        can_manage = (
            is_org_admin
            or is_batch_admin
        )

        if not (
            can_manage
            or is_owner
            or is_assigned
        ):
            raise ForbiddenException(
                "You do not have permission to modify this query."
            )

    return scope


def require_query_list_access(
    db: Session,
    user: User,
):
    """
    Validate access to the complete query listing.
    """

    scope = get_access_scope(db, user)

    if scope.is_super_admin:
        return scope

    if (
        "ORG_ADMIN" in scope.roles
        or "BATCH_ADMIN" in scope.roles
    ):
        return scope

    raise ForbiddenException(
        "You do not have permission to view all queries."
    )


def require_team_query_access(
    db: Session,
    user: User,
):
    """
    Validate access to team queries.
    """

    scope = get_access_scope(db, user)

    if scope.is_super_admin:
        return scope

    if (
        "ORG_ADMIN" in scope.roles
        or "BATCH_ADMIN" in scope.roles
    ):
        return scope

    raise ForbiddenException(
        "You do not have permission to view team queries."
    )


def require_dashboard_access(
    db: Session,
    user: User,
):
    """
    Validate access to query dashboard and analytics.
    """

    scope = get_access_scope(db, user)

    if scope.is_super_admin:
        return scope

    if (
        "ORG_ADMIN" in scope.roles
        or "BATCH_ADMIN" in scope.roles
    ):
        return scope

    raise ForbiddenException(
        "You do not have permission to view query analytics."
    )

from dataclasses import dataclass, field
from typing import Set
from uuid import UUID
from sqlalchemy.orm import Session

from app.organization_members.models import OrganizationMember
from app.users.models import User


@dataclass
class AccessScope:
    is_super_admin: bool = False
    organization_ids: Set[UUID] = field(default_factory=set)
    batch_ids: Set[UUID] = field(default_factory=set)
    member_ids: Set[UUID] = field(default_factory=set)
    user_ids: Set[UUID] = field(default_factory=set)
    roles: Set[str] = field(default_factory=set)


from app.rbac.dependencies import is_super_admin, normalize_role_code
from app.rbac.policies import RoleCode


def get_access_scope(
    db: Session,
    current_user: User,
) -> AccessScope:
    """
    Resolve user's access scope including organization memberships and roles.
    """
    if is_super_admin(current_user, db=db):
        return AccessScope(
            is_super_admin=True,
            user_ids={current_user.id} if current_user and hasattr(current_user, "id") else set(),
            roles={RoleCode.SUPER_ADMIN.value},
        )

    if not current_user or not hasattr(current_user, "id"):
        return AccessScope()

    memberships = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .all()
    )

    if not memberships:
        return AccessScope(
            user_ids={current_user.id},
        )

    org_ids = {m.organization_id for m in memberships if m.organization_id is not None}
    from app.batches.models import BatchMember
    batch_memberships = (
        db.query(BatchMember)
        .filter(
            BatchMember.user_id == current_user.id,
            BatchMember.is_deleted.is_(False),
            BatchMember.is_active.is_(True),
        )
        .all()
    )
    batch_ids = {bm.batch_id for bm in batch_memberships if bm.batch_id is not None}
    member_ids = {m.id for m in memberships}
    user_ids = {current_user.id}
    roles = set()

    for m in memberships:
        if m.role and m.role.name:
            normalized_role = normalize_role_code(m.role.name)
            roles.add(normalized_role)

    return AccessScope(
        is_super_admin=False,
        organization_ids=org_ids,
        batch_ids=batch_ids,
        member_ids=member_ids,
        user_ids=user_ids,
        roles=roles,
    )

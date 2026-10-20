from uuid import UUID

from sqlalchemy.orm import Session, joinedload, selectinload

from app.my_okr.models import OKR
from app.organization_members.models import OrganizationMember


def get_organization_members(
    db: Session,
    organization_id: UUID,
) -> list[OrganizationMember]:
    """Return every active, non-deleted member of an organization."""
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .options(
            joinedload(OrganizationMember.user),
            joinedload(OrganizationMember.organization),
        )
        .all()
    )


def get_organization_okrs(
    db: Session,
    organization_id: UUID,
) -> list[OKR]:
    """Get non-deleted OKRs assigned to active members of an organization."""
    return (
        db.query(OKR)
        .join(
            OrganizationMember,
            OrganizationMember.id == OKR.assigned_to,
        )
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
            OKR.is_deleted.is_(False),
        )
        .options(
            joinedload(OKR.assignee).joinedload(OrganizationMember.user),
            joinedload(OKR.assignee).joinedload(OrganizationMember.organization),
            selectinload(OKR.weekly_updates),
        )
        .all()
    )


def get_user_organization(
    db: Session,
    user_id: UUID,
) -> OrganizationMember | None:
    """Get an active organization membership for the current user."""
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .order_by(OrganizationMember.joined_at.desc())
        .first()
    )

from uuid import UUID

from sqlalchemy.orm import Session, joinedload, selectinload

from app.batches.models import Batch
from app.my_okr.models import OKR
from app.organization_members.models import OrganizationMember


def get_active_organization_membership(
    db: Session,
    user_id: UUID,
) -> OrganizationMember | None:
    """
    Get the current user's active organization membership.
    """
    return (
        db.query(OrganizationMember)
        .options(
            joinedload(OrganizationMember.organization),
            joinedload(OrganizationMember.user),
            joinedload(OrganizationMember.role),
        )
        .filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active.is_(True),
            OrganizationMember.is_deleted.is_(False),
        )
        .order_by(OrganizationMember.joined_at.desc())
        .first()
    )


def get_batch_for_organization(
    db: Session,
    batch_id: UUID,
    organization_id: UUID,
) -> Batch | None:
    """
    Verify that the requested batch belongs to the current organization.
    """
    return (
        db.query(Batch)
        .filter(
            Batch.id == batch_id,
            Batch.organization_id == organization_id,
            Batch.is_active.is_(True),
            Batch.is_deleted.is_(False),
        )
        .first()
    )


def get_performance_okrs(
    db: Session,
    organization_id: UUID,
    batch_id: UUID | None = None,
) -> list[OKR]:
    """
    Fetch active OKRs belonging to an organization.

    If batch_id is provided, only OKRs from that batch are returned.

    Weekly updates and tracker entries are eagerly loaded so the
    Performance API does not generate N+1 queries.
    """
    query = (
        db.query(OKR)
        .join(
            OrganizationMember,
            OrganizationMember.id == OKR.assigned_to,
        )
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.is_active.is_(True),
            OrganizationMember.is_deleted.is_(False),
            OKR.is_deleted.is_(False),
            OKR.is_active.is_(True),
        )
        .options(
            joinedload(OKR.assignee).joinedload(
                OrganizationMember.user
            ),
            selectinload(OKR.weekly_updates),
            selectinload(OKR.tracker_entries),
        )
    )

    if batch_id is not None:
        query = query.filter(OKR.batch_id == batch_id)

    return query.order_by(OKR.created_at.desc()).all()
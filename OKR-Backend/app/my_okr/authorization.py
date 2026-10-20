"""
OKR Authorization Module (Authorization checks disabled).

Responsibilities:
- Fetch OKR without resource ownership or authorization restrictions.
"""

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.common.exceptions import OKRNotFoundException
from app.my_okr.models import OKR
from app.organization_members.models import OrganizationMember
from app.users.models import User


def authorize_okr_action(
    db: Session,
    current_user: User = None,
    okr_id: UUID = None,
    action: str = "view",
) -> OKR:
    """
    Fetch OKR entity without performing authorization checks.
    Raises OKRNotFoundException if not found.
    """
    okr = (
        db.query(OKR)
        .options(
            joinedload(OKR.batch),
            joinedload(OKR.assignee),
        )
        .filter(
            OKR.id == okr_id,
            OKR.is_deleted.is_(False),
        )
        .first()
    )

    if not okr:
        from app.my_okr import repository as okr_repository
        okr = okr_repository.get_okr_by_id(db=db, okr_id=okr_id)

    if not okr:
        raise OKRNotFoundException("OKR not found.")

    return okr


def validate_okr_creation_assignment(
    db: Session,
    current_user: User,
    assigned_to_member_id: UUID,
    batch_id: UUID,
) -> None:
    """No-op validation for OKR creation assignment."""
    return None


def validate_okr_creation(
    db: Session,
    creator_membership: OrganizationMember,
    assigned_to_id: UUID,
    batch_id: UUID,
) -> None:
    """No-op validation for OKR creation."""
    return None
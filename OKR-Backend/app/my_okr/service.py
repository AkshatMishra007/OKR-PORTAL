from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.common.exceptions import (
    ForbiddenException,
    OKRAlreadyExistsException,
    OKRNotFoundException,
    UserNotFoundException,
)

from app.batches.models import Batch, BatchStatus
from app.organization_members.models import OrganizationMember
from app.users.models import User

from app.my_okr import repository as okr_repository
from app.my_okr.models import OKR
from app.my_okr.schemas import (
    OKRCreate,
    OKRUpdate,
)


from app.my_okr.authorization import (
    authorize_okr_action,
    validate_okr_creation,
    validate_okr_creation_assignment,
)
from app.rbac.dependencies import normalize_role_code
from app.rbac.policies import RoleCode

from app.tracker_entries import repository as tracker_repository
from app.tracker_entries.service import calculate_okr_progress


def _enrich_okr_progress(db: Session, okr: OKR, agg_data: dict | None = None) -> OKR:
    """
    Attach calculated progress and tracker metrics onto the OKR model instance.
    """
    if okr:
        progress_info = calculate_okr_progress(okr=okr, db=db, agg_data=agg_data)
        for key, value in progress_info.items():
            setattr(okr, key, value)
    return okr


def _enrich_okrs_bulk(db: Session, okrs: list[OKR]) -> list[OKR]:
    """
    Bulk enrich a list of OKRs with tracker aggregation in 1 DB query (avoids N+1).
    """
    if not okrs:
        return []
    okr_ids = [okr.id for okr in okrs]
    agg_mapping = tracker_repository.get_tracker_aggregates_for_okrs(db=db, okr_ids=okr_ids)
    for okr in okrs:
        _enrich_okr_progress(db=db, okr=okr, agg_data=agg_mapping.get(okr.id))
    return okrs


def create_okr(
    db: Session,
    okr_data: OKRCreate,
    current_user,
    current_membership: OrganizationMember | None = None,
) -> OKR:
    """
    Create new OKR after validating domain logic constraints.
    """
    validate_tracker(
        okr_type=okr_data.okr_type,
        tracker_enabled=okr_data.tracker_enabled,
    )

    batch = db.query(Batch).filter(Batch.id == okr_data.batch_id, Batch.is_deleted.is_(False)).first()
    if not batch:
        raise ForbiddenException("Invalid batch.")

    if batch.status == "CLOSED":
        raise ForbiddenException(
            f"Cannot modify data because the {batch.name} batch is closed and read-only."
        )

    target_member = (
        db.query(OrganizationMember)
        .filter(
            (OrganizationMember.id == okr_data.assigned_to) | (OrganizationMember.user_id == okr_data.assigned_to),
            OrganizationMember.organization_id == batch.organization_id,
            OrganizationMember.is_deleted.is_(False),
        )
        .first()
    )
    if not target_member:
        raise ForbiddenException("Assigned user is not a valid organization member.")

    okr_data_for_repo = okr_data.model_copy(update={"assigned_to": target_member.id})

    existing_okr = okr_repository.get_duplicate_okr(
        db=db,
        batch_id=okr_data.batch_id,
        assigned_to=target_member.id,
        objective=okr_data.objective,
    )

    if existing_okr:
        raise OKRAlreadyExistsException(
            "An OKR already exists for this user in this batch."
        )

    created_okr = okr_repository.create_okr(
        db=db,
        okr_data=okr_data_for_repo,
        created_by=getattr(current_user, "id", None),
    )
    return _enrich_okr_progress(db=db, okr=created_okr)


def get_okrs(
    db: Session,
    current_user=None,
    current_membership: OrganizationMember | None = None,
    organization_id: UUID | None = None,
    batch_id: UUID | None = None,
    assigned_to: UUID | None = None,
    user_id: UUID | None = None,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    status: str | None = None,
    tracker_enabled: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
):
    get_kwargs = {
        "organization_id": organization_id,
        "batch_id": batch_id,
        "assigned_to": assigned_to,
        "user_id": user_id,
        "page": page,
        "size": size,
        "search": search,
    }
    if status is not None:
        get_kwargs["status"] = status
    if tracker_enabled is not None:
        get_kwargs["tracker_enabled"] = tracker_enabled
    if sort_by is not None:
        get_kwargs["sort_by"] = sort_by
    if sort_order is not None:
        get_kwargs["sort_order"] = sort_order

    okrs, total = okr_repository.get_okrs(
        db=db,
        **get_kwargs,
    )

    enriched_okrs = _enrich_okrs_bulk(db=db, okrs=okrs)

    total_pages = (total + size - 1) // size if total > 0 else 1

    return {
        "data": enriched_okrs,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def get_okrs_by_user(
    db: Session,
    user_id: UUID,
    current_user=None,
    current_membership: OrganizationMember | None = None,
    organization_id: UUID | None = None,
    batch_id: UUID | None = None,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    status: str | None = None,
    tracker_enabled: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
):
    """
    Get OKRs assigned to a specific user across their organization memberships.
    """
    user = db.query(User).filter(User.id == user_id, User.is_deleted.is_(False)).first()
    if not user:
        raise UserNotFoundException("User not found.")

    return get_okrs(
        db=db,
        current_user=current_user,
        current_membership=current_membership,
        organization_id=organization_id,
        batch_id=batch_id,
        assigned_to=None,
        user_id=user_id,
        page=page,
        size=size,
        search=search,
        status=status,
        tracker_enabled=tracker_enabled,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_okr(
    db: Session,
    okr_id: UUID,
    current_user=None,
) -> OKR:

    okr = okr_repository.get_okr_by_id(
        db=db,
        okr_id=okr_id,
    )

    if not okr:
        raise OKRNotFoundException(
            "OKR not found."
        )

    return _enrich_okr_progress(db=db, okr=okr)


def update_okr(
    db: Session,
    okr_id: UUID,
    okr_data: OKRUpdate,
    current_user,
) -> OKR:

    okr = okr_repository.get_okr_by_id(
        db=db,
        okr_id=okr_id,
    )
    if not okr:
        raise OKRNotFoundException("OKR not found.")

    validate_batch_status(okr)

    update_data = okr_data.model_dump(
        exclude_unset=True
    )

    validate_tracker(
        okr_type=update_data.get(
            "okr_type",
            okr.okr_type
        ),
        tracker_enabled=update_data.get(
            "tracker_enabled",
            okr.tracker_enabled
        ),
    )

    updated_okr = okr_repository.update_okr(
        db=db,
        okr=okr,
        okr_data=okr_data,
        updated_by=current_user.id if current_user else None,
    )
    return _enrich_okr_progress(db=db, okr=updated_okr)


def delete_okr(
    db: Session,
    okr_id: UUID,
    current_user,
) -> OKR:

    okr = okr_repository.get_okr_by_id(
        db=db,
        okr_id=okr_id,
    )
    if not okr:
        raise OKRNotFoundException("OKR not found.")

    validate_batch_status(okr)

    deleted_okr = okr_repository.soft_delete_okr(
        db=db,
        okr=okr,
        deleted_by=current_user.id if current_user else None,
    )
    return _enrich_okr_progress(db=db, okr=deleted_okr)

# =====================================================
# VALIDATIONS
# =====================================================


def validate_tracker(
    okr_type: str,
    tracker_enabled: bool,
):
    allowed_tracker_types = {
        "PROFESSIONAL",
        "PERSONAL",
    }

    normalized_okr_type = (okr_type or "").strip().upper()

    if (
        tracker_enabled
        and normalized_okr_type not in allowed_tracker_types
    ):
        raise ForbiddenException(
            "Tracker can only be enabled for Professional or Personal OKRs."
        )


def validate_batch(
    db: Session,
    batch_id: UUID,
):

    batch = (
        db.query(Batch)
        .filter(
            Batch.id == batch_id
        )
        .first()
    )

    if not batch:
        raise ForbiddenException(
            "Invalid batch."
        )


def validate_assigned_member(
    db: Session,
    assigned_to: UUID,
):

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == assigned_to
        )
        .first()
    )

    if not member:
        raise ForbiddenException(
            "Assigned user is not a valid organization member."
        )


def validate_batch_status(
    okr: OKR,
):
    """
    Prevent modification after batch closure.
    """

    if (
        okr.batch
        and (okr.batch.status == "CLOSED" or okr.batch.status == BatchStatus.CLOSED)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify data because the {okr.batch.name} batch is closed and read-only.",
        )
from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session, joinedload


from app.batches.models import Batch
from app.organization_members.models import OrganizationMember
from app.my_okr.models import OKR
from app.my_okr.schemas import (
    OKRCreate,
    OKRUpdate,
)

def get_okr_joined_options():
    return (
        joinedload(OKR.batch).joinedload(Batch.organization),
        joinedload(OKR.assignee).joinedload(OrganizationMember.user),
        joinedload(OKR.assignee).joinedload(OrganizationMember.role),
    )




def create_okr(
    db: Session,
    okr_data: OKRCreate,
    created_by: UUID | None = None,
) -> OKR:

    okr = OKR(
        batch_id=okr_data.batch_id,
        assigned_to=okr_data.assigned_to,
        objective=okr_data.objective,
        target=okr_data.target,
        key_results=okr_data.key_results,
        okr_type=okr_data.okr_type,
        tracker_enabled=okr_data.tracker_enabled,
        status="ACTIVE",
        created_by=created_by,
    )

    db.add(okr)
    db.commit()
    db.refresh(okr)

    return get_okr_by_id(db, okr.id) or okr


def get_okr_by_id(
    db: Session,
    okr_id: UUID,
) -> OKR | None:

    query = (
        select(OKR)
        .options(*get_okr_joined_options())
        .where(
            OKR.id == okr_id,
            OKR.is_deleted.is_(False),
        )
    )

    return db.execute(query).scalar_one_or_none()


def get_duplicate_okr(
    db: Session,
    batch_id: UUID,
    assigned_to: UUID,
    objective: str,
) -> OKR | None:

    query = (
        select(OKR)
        .options(*get_okr_joined_options())
        .where(
            OKR.batch_id == batch_id,
            OKR.assigned_to == assigned_to,
            OKR.objective == objective,
            OKR.is_deleted.is_(False),
        )
    )

    return db.execute(query).scalar_one_or_none()


from app.common.query import validate_and_apply_sorting

ALLOWED_OKR_SORT_FIELDS = {
    "objective": OKR.objective,
    "okr_type": OKR.okr_type,
    "status": OKR.status,
    "tracker_enabled": OKR.tracker_enabled,
    "created_at": OKR.created_at,
    "updated_at": OKR.updated_at,
}


def get_okrs(
    db: Session,
    organization_id: UUID | None = None,
    batch_id: UUID | None = None,
    assigned_to: UUID | None = None,
    user_id: UUID | None = None,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    status: str | None = None,
    tracker_enabled: bool | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
) -> tuple[list[OKR], int]:

    query = select(OKR).where(
        OKR.is_deleted.is_(False)
    )

    if organization_id:
        query = query.where(
            or_(
                OKR.batch.has(Batch.organization_id == organization_id),
                OKR.assignee.has(OrganizationMember.organization_id == organization_id),
            )
        )

    if batch_id:
        query = query.where(
            OKR.batch_id == batch_id
        )

    if assigned_to:
        query = query.where(
            or_(
                OKR.assigned_to == assigned_to,
                OKR.assignee.has(OrganizationMember.user_id == assigned_to),
            )
        )

    if user_id:
        query = query.where(
            or_(
                OKR.assignee.has(OrganizationMember.user_id == user_id),
                OKR.assigned_to == user_id,
            )
        )


    if search:
        query = query.where(
            (OKR.objective.ilike(f"%{search}%"))
            | (OKR.target.ilike(f"%{search}%"))
            | (OKR.key_results.ilike(f"%{search}%"))
        )

    if status:
        query = query.where(OKR.status == status)

    if tracker_enabled is not None:
        query = query.where(OKR.tracker_enabled == tracker_enabled)

    # Total records before pagination
    total = db.execute(
        select(func.count())
        .select_from(query.subquery())
    ).scalar_one()

    query = validate_and_apply_sorting(
        query=query,
        model=OKR,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_OKR_SORT_FIELDS,
        default_sort_column=OKR.created_at,
    )

    query = (
        query
        .options(*get_okr_joined_options())
        .offset(
            (page - 1) * size
        )
        .limit(size)
    )

    okrs = (
        db.execute(query)
        .unique()
        .scalars()
        .all()
    )


    return list(okrs), total


def update_okr(
    db: Session,
    okr: OKR,
    okr_data: OKRUpdate,
    updated_by: UUID | None = None,
) -> OKR:

    update_data = okr_data.model_dump(
        exclude_unset=True,
    )


    for field, value in update_data.items():
        setattr(
            okr,
            field,
            value,
        )


    okr.updated_by = updated_by
    okr.updated_at = datetime.now(UTC)


    db.commit()
    db.refresh(okr)

    return get_okr_by_id(db, okr.id) or okr


def soft_delete_okr(
    db: Session,
    okr: OKR,
    deleted_by: UUID | None = None,
) -> OKR:

    okr.is_deleted = True
    okr.is_active = False
    okr.deleted_at = datetime.now(UTC)
    okr.updated_by = deleted_by
    okr.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(okr)

    return get_okr_by_id(db, okr.id) or okr
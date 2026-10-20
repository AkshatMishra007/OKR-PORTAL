"""
FOGS & Hurdles repository layer.
"""

from uuid import UUID
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.query import paginate_query, validate_and_apply_sorting
from app.fogs_hurdles.models import FogsHurdle
from app.fogs_hurdles.schemas import FogsHurdleCreate, FogsHurdleUpdate


def create_fogs_hurdle(
    db: Session,
    okr_id: UUID,
    fogs_hurdle_data: FogsHurdleCreate,
    created_by: UUID | None = None,
) -> FogsHurdle:
    hurdle = FogsHurdle(
        okr_id=okr_id,
        fogs_hurdles=fogs_hurdle_data.fogs_hurdles,
        action_points=fogs_hurdle_data.action_points,
        created_by=created_by,
    )
    db.add(hurdle)
    db.commit()
    db.refresh(hurdle)
    return hurdle


def get_fogs_hurdle_by_id(
    db: Session,
    fogs_hurdle_id: UUID,
) -> FogsHurdle | None:
    return (
        db.query(FogsHurdle)
        .filter(
            FogsHurdle.id == fogs_hurdle_id,
            FogsHurdle.is_deleted.is_(False),
        )
        .first()
    )


def get_fogs_hurdles_by_okr(
    db: Session,
    okr_id: UUID,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "desc",
) -> tuple[list[FogsHurdle], int]:
    query = db.query(FogsHurdle).filter(
        FogsHurdle.okr_id == okr_id,
        FogsHurdle.is_deleted.is_(False),
    )

    if search:
        query = query.filter(
            or_(
                FogsHurdle.fogs_hurdles.ilike(f"%{search}%"),
                FogsHurdle.action_points.ilike(f"%{search}%"),
            )
        )

    allowed_sort_fields = {
        "created_at": FogsHurdle.created_at,
        "updated_at": FogsHurdle.updated_at,
        "fogs_hurdles": FogsHurdle.fogs_hurdles,
    }

    query = validate_and_apply_sorting(
        query=query,
        model=FogsHurdle,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=allowed_sort_fields,
        default_sort_column=FogsHurdle.created_at,
    )

    items, meta = paginate_query(query=query, page=page, size=size)
    return list(items), meta["total"]


def update_fogs_hurdle(
    db: Session,
    fogs_hurdle: FogsHurdle,
    fogs_hurdle_data: FogsHurdleUpdate,
    updated_by: UUID | None = None,
) -> FogsHurdle:
    update_data = fogs_hurdle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fogs_hurdle, field, value)

    if updated_by:
        fogs_hurdle.updated_by = updated_by

    db.commit()
    db.refresh(fogs_hurdle)
    return fogs_hurdle


def soft_delete_fogs_hurdle(
    db: Session,
    fogs_hurdle: FogsHurdle,
    deleted_by: UUID | None = None,
) -> FogsHurdle:
    fogs_hurdle.is_deleted = True
    if deleted_by:
        fogs_hurdle.updated_by = deleted_by
    db.commit()
    db.refresh(fogs_hurdle)
    return fogs_hurdle

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.batches.schemas import (
    BatchCreate,
    BatchDetailResponse,
    BatchListResponse,
    BatchResponse,
    BatchUpdate,
)
from app.batches.service import BatchService
from app.core.database import get_db
from app.users.models import User


from app.rbac.dependencies import require_permission

router = APIRouter(
    prefix="/batches",
    tags=["Batches"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_batch(
    batch_data: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("batch.create")),
):
    service = BatchService(db)

    return service.create_batch(
        batch_data=batch_data,
        current_user=current_user,
    )


from app.batches.models import Quarter, BatchStatus

@router.get(
    "/",
    response_model=BatchListResponse,
)
def get_batches(
    organization_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    quarter: Quarter | None = Query(default=None),
    batch_status: BatchStatus | None = Query(default=None, alias="status"),
    year: int | None = Query(default=None),
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("batch.view")),
):
    service = BatchService(db)

    return service.get_batches(
        current_user=current_user,
        organization_id=organization_id,
        search=search,
        quarter=quarter,
        status=batch_status,
        year=year,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size,
    )


@router.get(
    "/{batch_id}",
    response_model=BatchDetailResponse,
)
def get_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("batch.view")),
):
    service = BatchService(db)

    return service.get_batch(
        batch_id=batch_id,
        current_user=current_user,
    )


@router.put(
    "/{batch_id}",
    response_model=BatchResponse,
)
def update_batch(
    batch_id: UUID,
    batch_data: BatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("batch.update")),
):
    service = BatchService(db)

    return service.update_batch(
        batch_id=batch_id,
        batch_data=batch_data,
        current_user=current_user,
    )


@router.post(
    "/{batch_id}/close",
    response_model=BatchDetailResponse,
)
def close_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("batch.manage")),
):
    service = BatchService(db)

    return service.close_batch(
        batch_id=batch_id,
        current_user=current_user,
    )


@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("batch.delete")),
):
    service = BatchService(db)

    service.delete_batch(
        batch_id=batch_id,
        current_user=current_user,
    )

    return None
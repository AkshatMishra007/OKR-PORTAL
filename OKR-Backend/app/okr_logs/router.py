"""
FastAPI Router endpoints for OKR Logs.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.common.schemas import ResponseSchema
from app.core.database import get_db
from app.okr_logs.schemas import OkrLogResponse
from app.okr_logs.service import OkrLogService

router = APIRouter(
    prefix="/okr-logs",
    tags=["OKR Logs"],
)


@router.get(
    "/",
    response_model=ResponseSchema[list[OkrLogResponse]],
    status_code=status.HTTP_200_OK,
)
def list_okr_logs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve OKR audit logs with pagination.
    """
    service = OkrLogService(db)
    logs = service.list_logs(skip=skip, limit=limit)
    return ResponseSchema(
        success=True,
        message="OKR logs retrieved successfully",
        data=logs,
    )


@router.get(
    "/user/{user_id}",
    response_model=ResponseSchema[list[OkrLogResponse]],
    status_code=status.HTTP_200_OK,
)
def get_user_okr_logs(
    user_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve OKR logs for a given user.
    """
    service = OkrLogService(db)
    logs = service.get_logs_by_user(user_id=user_id, limit=limit)
    return ResponseSchema(
        success=True,
        message="User OKR logs retrieved successfully",
        data=logs,
    )


@router.get(
    "/week/{weekly_no}",
    response_model=ResponseSchema[list[OkrLogResponse]],
    status_code=status.HTTP_200_OK,
)
def get_week_okr_logs(
    weekly_no: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retrieve OKR logs for a given week.
    """
    service = OkrLogService(db)
    logs = service.get_logs_by_week(weekly_no=weekly_no, limit=limit)
    return ResponseSchema(
        success=True,
        message="Weekly OKR logs retrieved successfully",
        data=logs,
    )

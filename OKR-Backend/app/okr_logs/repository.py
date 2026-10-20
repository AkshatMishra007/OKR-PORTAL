"""
Repository layer for OKR Logs.
Handles direct database access for OkrLog model.
"""
from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy.orm import Session

from app.okr_logs.models import OkrLog
from app.okr_logs.schemas import OkrLogCreate


def create_log(
    db: Session,
    log_data: OkrLogCreate,
    created_by: UUID | None = None,
) -> OkrLog:
    """
    Create a new OKR audit log record and persist to DB.
    """
    log = OkrLog(
        weekly_no=log_data.weekly_no,
        current_user=log_data.current_user,
        datetime=log_data.datetime or datetime.now(UTC),
        created_by=created_by or log_data.current_user,
        updated_by=created_by or log_data.current_user,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_logs_by_user(
    db: Session,
    user_id: UUID,
    limit: int = 50,
) -> list[OkrLog]:
    """
    Retrieve OKR logs for a specific user ordered by creation date.
    """
    return (
        db.query(OkrLog)
        .filter(OkrLog.current_user == user_id, OkrLog.is_deleted.is_(False))
        .order_by(OkrLog.created_at.desc())
        .limit(limit)
        .all()
    )


def get_logs_by_week(
    db: Session,
    weekly_no: int,
    limit: int = 50,
) -> list[OkrLog]:
    """
    Retrieve OKR logs for a specific week number.
    """
    return (
        db.query(OkrLog)
        .filter(OkrLog.weekly_no == weekly_no, OkrLog.is_deleted.is_(False))
        .order_by(OkrLog.created_at.desc())
        .limit(limit)
        .all()
    )


def list_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
) -> list[OkrLog]:
    """
    List OKR audit logs with pagination.
    """
    return (
        db.query(OkrLog)
        .filter(OkrLog.is_deleted.is_(False))
        .order_by(OkrLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

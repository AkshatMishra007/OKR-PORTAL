"""
Service layer for OKR Logs.
Coordinates business logic and access control for OKR audit logging.
"""
from uuid import UUID
from sqlalchemy.orm import Session

from app.okr_logs import repository as okr_log_repository
from app.okr_logs.models import OkrLog
from app.okr_logs.schemas import OkrLogCreate


class OkrLogService:
    """
    Service for querying and recording OKR audit logs.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self,
        log_data: OkrLogCreate,
        current_user=None,
    ) -> OkrLog:
        """
        Record an OKR log entry.
        """
        creator_id = getattr(current_user, "id", None) if current_user else None
        return okr_log_repository.create_log(
            db=self.db,
            log_data=log_data,
            created_by=creator_id,
        )

    def get_logs_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> list[OkrLog]:
        """
        Retrieve OKR logs for a user.
        """
        return okr_log_repository.get_logs_by_user(
            db=self.db,
            user_id=user_id,
            limit=limit,
        )

    def get_logs_by_week(
        self,
        weekly_no: int,
        limit: int = 50,
    ) -> list[OkrLog]:
        """
        Retrieve OKR logs for a specific week number.
        """
        return okr_log_repository.get_logs_by_week(
            db=self.db,
            weekly_no=weekly_no,
            limit=limit,
        )

    def list_logs(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[OkrLog]:
        """
        List OKR logs with pagination.
        """
        return okr_log_repository.list_logs(
            db=self.db,
            skip=skip,
            limit=limit,
        )

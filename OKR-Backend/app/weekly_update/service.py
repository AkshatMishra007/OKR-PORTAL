from uuid import UUID

from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from app.batches.models import BatchStatus
from app.common.exceptions import (
    OKRNotFoundException,
    WeeklyUpdateAlreadyExistsException,
    WeeklyUpdateNotFoundException,
)
from app.my_okr import repository as okr_repository
from app.my_okr.authorization import authorize_okr_action
from app.weekly_update import repository as weekly_update_repository
from app.weekly_update.models import WeeklyUpdate
from app.weekly_update.schemas import WeeklyUpdateCreate, WeeklyUpdateUpdate


class WeeklyUpdateService:

    def __init__(self, db: Session):
        self.db = db

    def create_weekly_update(
        self,
        okr_id: UUID,
        update_data: WeeklyUpdateCreate,
        current_user,
    ) -> WeeklyUpdate:
        """
        Create a weekly update for an OKR after checking parent OKR authorization and duplicate entries.
        """
        okr = okr_repository.get_okr_by_id(
            db=self.db,
            okr_id=okr_id,
        )
        if not okr:
            raise OKRNotFoundException("OKR not found.")
        if okr.batch and (okr.batch.status == BatchStatus.CLOSED or okr.batch.status == "CLOSED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify data because the {okr.batch.name} batch is closed and read-only.",
            )

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=okr_id,
                action="update",
            )

        # existing_update = weekly_update_repository.get_weekly_update_by_okr_and_week(
        #     db=self.db,
        #     okr_id=okr_id,
        #     week_number=update_data.week_number,
        # )
        # if existing_update:
        #     raise WeeklyUpdateAlreadyExistsException(
        #         "A weekly update for this week number already exists for this OKR."
        #     )

        return weekly_update_repository.create_weekly_update(
            db=self.db,
            okr_id=okr_id,
            update_data=update_data,
            created_by=current_user.id if current_user else None,
        )

    def get_weekly_update(
        self,
        update_id: UUID,
        current_user=None,
    ) -> WeeklyUpdate:
        """
        Fetch a single weekly update by ID.
        """
        update = weekly_update_repository.get_weekly_update_by_id(
            db=self.db,
            update_id=update_id,
        )
        if not update:
            raise WeeklyUpdateNotFoundException("Weekly update not found.")

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=update.okr_id,
                action="view",
            )

        return update

    def get_weekly_updates_for_okr(
        self,
        okr_id: UUID,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        min_progress: float | None = None,
        max_progress: float | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        current_user=None,
    ) -> dict:
        """
        Fetch paginated weekly updates for a specific OKR.
        """
        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=okr_id,
                action="view",
            )
        else:
            okr = okr_repository.get_okr_by_id(
                db=self.db,
                okr_id=okr_id,
            )
            if not okr:
                raise OKRNotFoundException("OKR not found.")

        get_kwargs = {
            "page": page,
            "size": size,
        }
        if search is not None:
            get_kwargs["search"] = search
        if min_progress is not None:
            get_kwargs["min_progress"] = min_progress
        if max_progress is not None:
            get_kwargs["max_progress"] = max_progress
        if sort_by is not None:
            get_kwargs["sort_by"] = sort_by
        if sort_order is not None:
            get_kwargs["sort_order"] = sort_order

        updates, total = weekly_update_repository.get_weekly_updates_by_okr(
            db=self.db,
            okr_id=okr_id,
            **get_kwargs,
        )

        total_pages = (total + size - 1) // size if total > 0 else 1

        return {
            "data": updates,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    def update_weekly_update(
        self,
        update_id: UUID,
        update_data: WeeklyUpdateUpdate,
        current_user,
    ) -> WeeklyUpdate:
        """
        Update an existing weekly update.
        """
        update = weekly_update_repository.get_weekly_update_by_id(
            db=self.db,
            update_id=update_id,
        )
        if not update:
            raise WeeklyUpdateNotFoundException("Weekly update not found.")

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=update.okr_id,
                action="update",
            )

        return weekly_update_repository.update_weekly_update(
            db=self.db,
            weekly_update=update,
            update_data=update_data,
            updated_by=current_user.id if current_user else None,
        )

    def delete_weekly_update(
        self,
        update_id: UUID,
        current_user,
    ) -> WeeklyUpdate:
        """
        Soft delete a weekly update.
        """
        update = weekly_update_repository.get_weekly_update_by_id(
            db=self.db,
            update_id=update_id,
        )
        if not update:
            raise WeeklyUpdateNotFoundException("Weekly update not found.")

        if current_user:
            authorize_okr_action(
                db=self.db,
                current_user=current_user,
                okr_id=update.okr_id,
                action="delete",
            )

        return weekly_update_repository.soft_delete_weekly_update(
            db=self.db,
            weekly_update=update,
            deleted_by=current_user.id if current_user else None,
        )

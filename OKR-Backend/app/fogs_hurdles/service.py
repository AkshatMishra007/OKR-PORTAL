"""
FOGS & Hurdles service layer.
"""

from uuid import UUID
from sqlalchemy.orm import Session, joinedload

from fastapi import HTTPException, status
from app.batches.models import Batch, BatchStatus
from app.common.exceptions import (
    FogsHurdleNotFoundException,
    ForbiddenException,
    OKRNotFoundException,
)
from app.fogs_hurdles import repository as fogs_hurdle_repository
from app.fogs_hurdles.schemas import FogsHurdleCreate, FogsHurdleUpdate
from app.my_okr import repository as okr_repository
from app.organization_members.models import OrganizationMember
from app.rbac.dependencies import is_super_admin, normalize_role_code
from app.rbac.policies import RoleCode
from app.users.models import User


class FogsHurdleService:
    def __init__(self, db: Session):
        self.db = db

    def _check_closed_batch(self, okr) -> None:
        if not okr:
            return
        batch = getattr(okr, "batch", None)
        if not batch and hasattr(okr, "batch_id") and okr.batch_id:
            batch = self.db.query(Batch).filter(Batch.id == okr.batch_id).first()

        if batch:
            batch_status = getattr(batch, "status", None)
            if batch_status in (BatchStatus.CLOSED, "CLOSED"):
                batch_name = getattr(batch, "name", "Current")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot modify data because the {batch_name} batch is closed and read-only.",
                )

    def _validate_fogs_hurdle_access(
        self,
        current_user: User | None,
        okr,
        action: str = "view",
    ) -> None:
        if not current_user:
            return

        if is_super_admin(current_user, db=self.db):
            return

        if not okr:
            return

        # Resolve organization_id of the OKR
        org_id = None
        if hasattr(okr, "batch") and okr.batch:
            org_id = getattr(okr.batch, "organization_id", None)
        elif hasattr(okr, "batch_id") and okr.batch_id:
            b = self.db.query(Batch).filter(Batch.id == okr.batch_id).first()
            if b:
                org_id = b.organization_id

        if not org_id and hasattr(okr, "assignee") and okr.assignee:
            org_id = getattr(okr.assignee, "organization_id", None)

        caller_memberships = (
            self.db.query(OrganizationMember)
            .options(joinedload(OrganizationMember.role))
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_deleted.is_(False),
                OrganizationMember.is_active.is_(True),
            )
            .all()
        )

        if not caller_memberships:
            return

        # Check organization boundary
        if org_id:
            caller_org_memberships = [m for m in caller_memberships if m.organization_id == org_id]
            if not caller_org_memberships:
                raise ForbiddenException("You are not an active member of this organization.")
        else:
            caller_org_memberships = caller_memberships

        caller_roles = {
            normalize_role_code(m.role.name) for m in caller_org_memberships if m.role
        }

        # 1. ORG_ADMIN: Full authority within own organization
        if RoleCode.ORG_ADMIN.value in caller_roles:
            return

        # 2. BATCH_ADMIN: Scoped authority for assigned batch
        if RoleCode.BATCH_ADMIN.value in caller_roles:
            from app.batches.models import BatchMember
            caller_batch_memberships = (
                self.db.query(BatchMember)
                .filter(
                    BatchMember.user_id == current_user.id,
                    BatchMember.is_deleted.is_(False),
                    BatchMember.is_active.is_(True),
                )
                .all()
            )
            caller_batch_ids = {m.batch_id for m in caller_batch_memberships if m.batch_id is not None}
            okr_batch_id = getattr(okr, "batch_id", None)
            if okr_batch_id and okr_batch_id not in caller_batch_ids:
                raise ForbiddenException("Batch Admin cannot manage OKR hurdles outside assigned batch.")
            return

        # 3. EMPLOYEE:
        if RoleCode.EMPLOYEE.value in caller_roles or not caller_roles:
            caller_member_ids = {m.id for m in caller_org_memberships}

            # Mutations (create, update, delete): Must be assigned to this OKR or creator
            if action in ("create", "update", "delete"):
                assigned_to_id = getattr(okr, "assigned_to", None)
                assignee_obj = getattr(okr, "assignee", None)
                assignee_user_id = getattr(assignee_obj, "user_id", None) if assignee_obj else None
                created_by_id = getattr(okr, "created_by", None)

                is_assigned = (
                    (assigned_to_id and assigned_to_id in caller_member_ids)
                    or (assignee_user_id and assignee_user_id == current_user.id)
                    or (created_by_id and created_by_id == current_user.id)
                )
                if not is_assigned:
                    raise ForbiddenException("Employees can only modify FOGS & Hurdles on their own OKRs.")
                return

            # View: Allowed within batch cohort
            # okr_batch_id = getattr(okr, "batch_id", None)
            # if okr_batch_id and caller_batch_ids and okr_batch_id not in caller_batch_ids:
            #     raise ForbiddenException("Access denied to OKR hurdles outside your assigned batch.")
            return

    def create_fogs_hurdle(
        self,
        okr_id: UUID,
        hurdle_data: FogsHurdleCreate,
        current_user: User,
    ):
        okr = okr_repository.get_okr_by_id(db=self.db, okr_id=okr_id)
        if not okr:
            raise OKRNotFoundException("OKR not found.")

        self._check_closed_batch(okr)
        self._validate_fogs_hurdle_access(
            current_user=current_user,
            okr=okr,
            action="create",
        )

        user_id = getattr(current_user, "id", None)
        return fogs_hurdle_repository.create_fogs_hurdle(
            db=self.db,
            okr_id=okr_id,
            fogs_hurdle_data=hurdle_data,
            created_by=user_id,
        )

    def get_fogs_hurdle(self, fogs_hurdle_id: UUID, current_user: User | None = None):
        hurdle = fogs_hurdle_repository.get_fogs_hurdle_by_id(
            db=self.db,
            fogs_hurdle_id=fogs_hurdle_id,
        )
        if not hurdle:
            raise FogsHurdleNotFoundException("FOGS & Hurdle record not found.")

        if current_user:
            okr = okr_repository.get_okr_by_id(db=self.db, okr_id=hurdle.okr_id)
            if okr:
                self._validate_fogs_hurdle_access(
                    current_user=current_user,
                    okr=okr,
                    action="view",
                )

        return hurdle

    def get_fogs_hurdles_for_okr(
        self,
        okr_id: UUID,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        sort_by: str | None = "created_at",
        sort_order: str | None = "desc",
        current_user: User | None = None,
    ):
        okr = okr_repository.get_okr_by_id(db=self.db, okr_id=okr_id)
        if not okr:
            raise OKRNotFoundException("OKR not found.")

        if current_user:
            self._validate_fogs_hurdle_access(
                current_user=current_user,
                okr=okr,
                action="view",
            )

        records, total = fogs_hurdle_repository.get_fogs_hurdles_by_okr(
            db=self.db,
            okr_id=okr_id,
            page=page,
            size=size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return {
            "data": records,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
            },
        }

    def update_fogs_hurdle(
        self,
        fogs_hurdle_id: UUID,
        update_data: FogsHurdleUpdate,
        current_user: User,
    ):
        hurdle = fogs_hurdle_repository.get_fogs_hurdle_by_id(
            db=self.db,
            fogs_hurdle_id=fogs_hurdle_id,
        )
        if not hurdle:
            raise FogsHurdleNotFoundException("FOGS & Hurdle record not found.")

        okr = okr_repository.get_okr_by_id(db=self.db, okr_id=hurdle.okr_id)
        if okr:
            self._check_closed_batch(okr)
            if current_user:
                self._validate_fogs_hurdle_access(
                    current_user=current_user,
                    okr=okr,
                    action="update",
                )

        user_id = getattr(current_user, "id", None)
        return fogs_hurdle_repository.update_fogs_hurdle(
            db=self.db,
            fogs_hurdle=hurdle,
            fogs_hurdle_data=update_data,
            updated_by=user_id,
        )

    def delete_fogs_hurdle(
        self,
        fogs_hurdle_id: UUID,
        current_user: User,
    ):
        hurdle = fogs_hurdle_repository.get_fogs_hurdle_by_id(
            db=self.db,
            fogs_hurdle_id=fogs_hurdle_id,
        )
        if not hurdle:
            raise FogsHurdleNotFoundException("FOGS & Hurdle record not found.")

        okr = okr_repository.get_okr_by_id(db=self.db, okr_id=hurdle.okr_id)
        if okr:
            self._check_closed_batch(okr)
            if current_user:
                self._validate_fogs_hurdle_access(
                    current_user=current_user,
                    okr=okr,
                    action="delete",
                )

        user_id = getattr(current_user, "id", None)
        return fogs_hurdle_repository.soft_delete_fogs_hurdle(
            db=self.db,
            fogs_hurdle=hurdle,
            deleted_by=user_id,
        )

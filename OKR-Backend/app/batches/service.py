from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.common.exceptions import (
    AppException,
    BatchAlreadyExistsException,
    BatchNotFoundException,
    ForbiddenException,
    OrganizationNotFoundException,
    RoleNotFoundException,
    UserNotFoundException,
)
from app.organization_members import repository as organization_member_repository
from app.organization_members.models import OrganizationMember
from app.organizations import repository as organization_repository
from app.rbac import repository as rbac_repository
from app.rbac.dependencies import is_super_admin, normalize_role_code
from app.rbac.policies import RoleCode
from fastapi import HTTPException, status
from app.batches import repository as batch_repository
from app.batches.models import Batch, BatchStatus
from app.batches.schemas import BatchCreate, BatchUpdate
from app.users import service as user_service


class BatchService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def _validate_batch_tenant_access(
        self,
        current_user,
        organization_id: UUID,
        batch_id: UUID | None = None,
        action: str = "view",
    ) -> None:
        if not current_user:
            return

        if is_super_admin(current_user, db=self.db):
            return

        caller_all_memberships = (
            self.db.query(OrganizationMember)
            .options(joinedload(OrganizationMember.role))
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_deleted.is_(False),
                OrganizationMember.is_active.is_(True),
            )
            .all()
        )

        if not caller_all_memberships:
            return

        caller_memberships = [m for m in caller_all_memberships if m.organization_id == organization_id]

        if not caller_memberships:
            raise ForbiddenException("You are not an active member of this organization.")

        caller_roles = {
            normalize_role_code(m.role.name) for m in caller_memberships if m.role
        }

        if RoleCode.ORG_ADMIN.value in caller_roles:
            return

        if RoleCode.BATCH_ADMIN.value in caller_roles:
            caller_batch_memberships = batch_repository.get_user_active_batch_memberships(
                db=self.db,
                user_id=current_user.id,
            )
            caller_batch_ids = {
                bm.batch_id for bm in caller_batch_memberships
            }
            if batch_id is not None and batch_id not in caller_batch_ids:
                raise ForbiddenException("Batch Admin cannot manage batches outside assigned batch.")
            if action in ("create", "delete"):
                raise ForbiddenException("Batch Admin cannot create or delete batches.")
            return

        raise ForbiddenException("Employees are not authorized to view or manage batches.")

    def create_batch(
        self,
        batch_data: BatchCreate,
        current_user,
    ) -> Batch:
        # Step 1: Validate tenant access
        self._validate_batch_tenant_access(
            current_user=current_user,
            organization_id=batch_data.organization_id,
            action="create",
        )

        # Step 2: Verify organization exists
        organization = organization_repository.get_organization_by_id(
            db=self.db,
            organization_id=batch_data.organization_id,
        )

        if not organization:
            raise OrganizationNotFoundException(
                "Organization not found."
            )

        # Step 3: Verify duplicate batch name/year/quarter rules
        existing_batch = batch_repository.get_batch_by_name_year_and_quarter(
            db=self.db,
            organization_id=batch_data.organization_id,
            name=batch_data.name,
            year=batch_data.year,
            quarter=batch_data.quarter,
        )

        if existing_batch:
            raise BatchAlreadyExistsException(
                "A batch already exists for the selected organization, year and quarter."
            )

        # Step 4: Normalize
        batch_user_ids = set(batch_data.batch_users or [])
        batch_admin_ids = set(batch_data.batch_admins or [])

        # Reject if the same user appears in both lists
        if batch_user_ids & batch_admin_ids:
            raise AppException(
                "User cannot be both Employee and Batch Admin in the same batch."
            )

        all_user_ids = batch_user_ids | batch_admin_ids

        # Step 5: Validate all supplied users exist
        for user_id in all_user_ids:
            try:
                user = user_service.get_user_by_id(self.db, user_id, current_user=current_user)
            except UserNotFoundException:
                raise UserNotFoundException(f"User not found: {user_id}")

        # Step 6: Validate every supplied user is an active member of the batch's organization using OrganizationMember
        for user_id in all_user_ids:
            org_member = organization_member_repository.get_member_by_user_and_organization(
                db=self.db,
                organization_id=batch_data.organization_id,
                user_id=user_id,
            )
            if not org_member or not org_member.is_active or org_member.is_deleted:
                raise AppException(
                    f"User {user_id} is not an active member of this organization."
                )

        employee_role = None
        if batch_user_ids:
            employee_role = self._get_employee_role()

        batch_admin_role = None
        if batch_admin_ids:
            batch_admin_role = self._get_batch_admin_role()

        # Step 8 Employee check: Employees can belong to only ONE active batch
        if employee_role:
            for user_id in batch_user_ids:
                existing_emp = batch_repository.get_employee_membership_in_other_batch(
                    db=self.db,
                    organization_id=batch_data.organization_id,
                    user_id=user_id,
                    employee_role_id=employee_role.id,
                )
                if existing_emp:
                    raise AppException(
                        "Employee is already assigned to another batch."
                    )

        current_user_id = current_user.id if current_user else None

        try:
            # Step 7: Create the Batch
            batch = batch_repository.create_batch(
                db=self.db,
                batch_data=batch_data,
                created_by=current_user_id,
            )

            # Step 8 â€” Employees
            if employee_role:
                for user_id in batch_user_ids:
                    existing_bm = batch_repository.get_batch_member(
                        db=self.db,
                        batch_id=batch.id,
                        user_id=user_id,
                    )
                    if existing_bm:
                        if existing_bm.role_id != employee_role.id:
                            raise AppException(
                                "User is already assigned to this batch with a different role."
                            )
                    else:
                        batch_repository.create_batch_member(
                            db=self.db,
                            batch_id=batch.id,
                            user_id=user_id,
                            role_id=employee_role.id,
                            created_by=current_user_id,
                        )

            # Step 9 â€” Batch Admins
            if batch_admin_role:
                for user_id in batch_admin_ids:
                    existing_bm = batch_repository.get_batch_member(
                        db=self.db,
                        batch_id=batch.id,
                        user_id=user_id,
                    )
                    if existing_bm:
                        if existing_bm.role_id != batch_admin_role.id:
                            raise AppException(
                                "User is already assigned to this batch with a different role."
                            )
                    else:
                        batch_repository.create_batch_member(
                            db=self.db,
                            batch_id=batch.id,
                            user_id=user_id,
                            role_id=batch_admin_role.id,
                            created_by=current_user_id,
                        )

            # Step 10: Commit transaction
            self.db.commit()
            self.db.refresh(batch)

            # Step 11: Return the batch with its users/admins loaded through BatchMember
            users, admins = self._get_batch_members_lists(batch.id)
            batch.users = users
            batch.admins = admins
            return batch
        except Exception:
            self.db.rollback()
            raise



    def _get_employee_role(self):
        role = (
            rbac_repository.get_role_by_name(self.db, "Employee")
            or rbac_repository.get_role_by_name(self.db, "employee")
            or rbac_repository.get_role_by_name(self.db, "EMPLOYEE")
        )
        if not role:
            raise RoleNotFoundException("Employee role not found.")
        return role

    def _get_batch_admin_role(self):
        role = (
            rbac_repository.get_role_by_name(self.db, "Batch Admin")
            or rbac_repository.get_role_by_name(self.db, "batch_admin")
            or rbac_repository.get_role_by_name(self.db, "BATCH_ADMIN")
        )
        if not role:
            raise RoleNotFoundException("Batch Admin role not found.")
        return role

    def _sync_batch_users(
        self,
        batch: Batch,
        requested_user_ids: list[UUID],
        employee_role,
        current_user,
    ):
        current_user_id = current_user.id if current_user else None
        existing_members = batch_repository.get_batch_members(
            db=self.db,
            batch_id=batch.id,
            role_id=employee_role.id,
            is_active=True,
        )

        active_map = {
            m.user_id: m for m in existing_members
        }
        target_ids = set(requested_user_ids)

        for user_id, member in active_map.items():
            if user_id not in target_ids:
                batch_repository.soft_delete_batch_member(
                    db=self.db,
                    member=member,
                    updated_by=current_user_id,
                )

        for user_id in target_ids:
            if user_id not in active_map:
                existing_member = batch_repository.get_batch_member(
                    db=self.db,
                    batch_id=batch.id,
                    user_id=user_id,
                )
                if existing_member and existing_member.role_id != employee_role.id:
                    raise AppException(
                        "User is already assigned to this batch with a different role."
                    )
                batch_repository.create_batch_member(
                    db=self.db,
                    batch_id=batch.id,
                    user_id=user_id,
                    role_id=employee_role.id,
                    created_by=current_user_id,
                )

    def _sync_batch_admins(
        self,
        batch: Batch,
        requested_user_ids: list[UUID],
        batch_admin_role,
        current_user,
    ):
        current_user_id = current_user.id if current_user else None
        existing_members = batch_repository.get_batch_members(
            db=self.db,
            batch_id=batch.id,
            role_id=batch_admin_role.id,
            is_active=True,
        )

        active_map = {
            m.user_id: m for m in existing_members
        }
        target_ids = set(requested_user_ids)

        for user_id, member in active_map.items():
            if user_id not in target_ids:
                batch_repository.soft_delete_batch_member(
                    db=self.db,
                    member=member,
                    updated_by=current_user_id,
                )

        for user_id in target_ids:
            if user_id not in active_map:
                existing_member = batch_repository.get_batch_member(
                    db=self.db,
                    batch_id=batch.id,
                    user_id=user_id,
                )
                if existing_member and existing_member.role_id != batch_admin_role.id:
                    raise AppException(
                        "User is already assigned to this batch with a different role."
                    )
                batch_repository.create_batch_member(
                    db=self.db,
                    batch_id=batch.id,
                    user_id=user_id,
                    role_id=batch_admin_role.id,
                    created_by=current_user_id,
                )

    def _get_batch_members_lists(self, batch_id: UUID) -> tuple[list, list]:
        try:
            employee_role = self._get_employee_role()
        except Exception:
            employee_role = None

        try:
            batch_admin_role = self._get_batch_admin_role()
        except Exception:
            batch_admin_role = None

        members = batch_repository.get_batch_members(
            db=self.db,
            batch_id=batch_id,
            is_active=True,
        )

        users = []
        admins = []

        for m in members:
            if m.user is None:
                continue
            if employee_role and m.role_id == employee_role.id:
                users.append(m.user)
            elif batch_admin_role and m.role_id == batch_admin_role.id:
                admins.append(m.user)

        return users, admins

    def get_batch(
        self,
        batch_id: UUID,
        current_user,
    ) -> dict:

        batch = batch_repository.get_batch_by_id(
            db=self.db,
            batch_id=batch_id,
        )

        if not batch:
            raise BatchNotFoundException(
                "Batch not found."
            )

        self._validate_batch_tenant_access(
            current_user=current_user,
            organization_id=batch.organization_id,
            batch_id=batch.id,
            action="view",
        )

        users, admins = self._get_batch_members_lists(batch_id)

        return {
            "data": {
                "id": batch.id,
                "organization_id": batch.organization_id,
                "name": batch.name,
                "year": batch.year,
                "quarter": batch.quarter,
                "start_date": batch.start_date,
                "end_date": batch.end_date,
                "meeting_day": batch.meeting_day,
                "status": batch.status,
                "is_active": batch.is_active,
                "created_by": batch.created_by,
                "updated_by": batch.updated_by,
                "created_at": batch.created_at,
                "updated_at": batch.updated_at,
                "users": users,
                "admins": admins,
            }
        }



    def get_batches(
        self,
        current_user,
        organization_id: UUID | None = None,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        quarter=None,
        status: str | None = None,
        year: int | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
    ):
        organization_ids = None
        batch_ids = None

        if current_user and not is_super_admin(current_user, db=self.db):
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

            if caller_memberships:
                allowed_org_ids = {m.organization_id for m in caller_memberships if m.organization_id}
                if organization_id and organization_id not in allowed_org_ids:
                    raise ForbiddenException("Access denied to batches in another organization.")

                caller_roles = {
                    normalize_role_code(m.role.name) for m in caller_memberships if m.role
                }

                if RoleCode.ORG_ADMIN.value in caller_roles:
                    if organization_id:
                        organization_ids = None
                    else:
                        organization_ids = list(allowed_org_ids)
                elif RoleCode.BATCH_ADMIN.value in caller_roles:
                    caller_batch_memberships = batch_repository.get_user_active_batch_memberships(
                        db=self.db,
                        user_id=current_user.id,
                    )
                    batch_ids = [bm.batch_id for bm in caller_batch_memberships]
                else:
                    raise ForbiddenException("Employees are not authorized to view batches.")

        get_kwargs = {
            "organization_id": organization_id,
            "organization_ids": organization_ids,
            "batch_ids": batch_ids,
            "page": page,
            "size": size,
            "search": search,
        }
        if quarter is not None:
            get_kwargs["quarter"] = quarter
        if status is not None:
            get_kwargs["status"] = status
        if year is not None:
            get_kwargs["year"] = year
        if sort_by is not None:
            get_kwargs["sort_by"] = sort_by
        if sort_order is not None:
            get_kwargs["sort_order"] = sort_order

        batches, total = batch_repository.get_batches(
            db=self.db,
            **get_kwargs,
        )

        for b in batches:
            u, a = self._get_batch_members_lists(b.id)
            b.users = u
            b.admins = a

        total_pages = (total + size - 1) // size if total > 0 else 1

        return {
            "data": batches,
            "pagination": {
                "page": page,
                "size": size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }


    def validate_batch_open(self, batch: Batch) -> None:
        if batch.status == BatchStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify data because the {batch.name} batch is closed and read-only.",
            )

    def close_batch(
        self,
        batch_id: UUID,
        current_user,
    ) -> dict:
        batch = batch_repository.get_batch_by_id(
            db=self.db,
            batch_id=batch_id,
        )

        if not batch:
            raise BatchNotFoundException(
                "Batch not found."
            )

        self._validate_batch_tenant_access(
            current_user=current_user,
            organization_id=batch.organization_id,
            batch_id=batch.id,
            action="update",
        )

        current_user_id = current_user.id if current_user else None

        batch.status = BatchStatus.CLOSED
        batch.closed_at = datetime.now(UTC)
        batch.closed_by = current_user_id
        batch.updated_by = current_user_id

        self.db.commit()
        self.db.refresh(batch)

        users, admins = self._get_batch_members_lists(batch_id)

        return {
            "data": {
                "id": batch.id,
                "organization_id": batch.organization_id,
                "name": batch.name,
                "year": batch.year,
                "quarter": batch.quarter,
                "start_date": batch.start_date,
                "end_date": batch.end_date,
                "meeting_day": batch.meeting_day,
                "status": batch.status,
                "is_active": batch.is_active,
                "created_by": batch.created_by,
                "updated_by": batch.updated_by,
                "closed_by": batch.closed_by,
                "closed_at": batch.closed_at,
                "created_at": batch.created_at,
                "updated_at": batch.updated_at,
                "users": users,
                "admins": admins,
            }
        }

    def update_batch(
        self,
        batch_id: UUID,
        batch_data: BatchUpdate,
        current_user,
    ) -> Batch:

        batch = batch_repository.get_batch_by_id(
            db=self.db,
            batch_id=batch_id,
        )

        if not batch:
            raise BatchNotFoundException(
                "Batch not found."
            )

        self._validate_batch_tenant_access(
            current_user=current_user,
            organization_id=batch.organization_id,
            batch_id=batch.id,
            action="update",
        )

        if batch.status == BatchStatus.CLOSED and batch_data.status != BatchStatus.ACTIVE:
            self.validate_batch_open(batch)

        updated_year = (
            batch_data.year
            if batch_data.year is not None
            else batch.year
        )

        updated_quarter = (
            batch_data.quarter
            if batch_data.quarter is not None
            else batch.quarter
        )

        updated_name = (
            batch_data.name
            if batch_data.name is not None
            else batch.name
        )

        existing_batch = batch_repository.get_batch_by_name_year_and_quarter(
            db=self.db,
            organization_id=batch.organization_id,
            name=updated_name,
            year=updated_year,
            quarter=updated_quarter,
        )

        if (
            existing_batch
            and existing_batch.id != batch.id
        ):
            raise BatchAlreadyExistsException(
                "A batch already exists for the selected year and quarter."
            )

        all_target_users = set()
        if batch_data.batch_users is not None:
            all_target_users.update(batch_data.batch_users)
        if batch_data.batch_admins is not None:
            all_target_users.update(batch_data.batch_admins)

        for user_id in all_target_users:
            try:
                user = user_service.get_user_by_id(self.db, user_id, current_user=current_user)
            except UserNotFoundException:
                raise UserNotFoundException(f"User not found: {user_id}")

            org_member = organization_member_repository.get_member_by_user_and_organization(
                db=self.db,
                organization_id=batch.organization_id,
                user_id=user_id,
            )
            if not org_member or not org_member.is_active or org_member.is_deleted:
                raise AppException(
                    f"User {user_id} is not an active member of this organization."
                )

        employee_role = None
        batch_admin_role = None

        if batch_data.batch_users is not None or batch_data.batch_admins is not None:
            employee_role = self._get_employee_role()
            batch_admin_role = self._get_batch_admin_role()

            active_batch_members = batch_repository.get_batch_members(
                db=self.db,
                batch_id=batch.id,
                is_active=True,
            )

            current_emp_user_ids = {
                m.user_id for m in active_batch_members
                if employee_role and m.role_id == employee_role.id
            }
            current_admin_user_ids = {
                m.user_id for m in active_batch_members
                if batch_admin_role and m.role_id == batch_admin_role.id
            }

            target_emp_user_ids = (
                set(batch_data.batch_users)
                if batch_data.batch_users is not None
                else current_emp_user_ids
            )
            target_admin_user_ids = (
                set(batch_data.batch_admins)
                if batch_data.batch_admins is not None
                else current_admin_user_ids
            )

            # Rule 1: User cannot be both Employee and Batch Admin in the same batch
            if target_emp_user_ids & target_admin_user_ids:
                raise AppException(
                    "User cannot be both Employee and Batch Admin in the same batch."
                )

        # Rule 2: Employee can only belong to one batch
        if batch_data.batch_users is not None and employee_role:
            for user_id in set(batch_data.batch_users):
                existing_emp = batch_repository.get_employee_membership_in_other_batch(
                    db=self.db,
                    organization_id=batch.organization_id,
                    user_id=user_id,
                    employee_role_id=employee_role.id,
                    current_batch_id=batch.id,
                )
                if existing_emp:
                    raise AppException(
                        "Employee is already assigned to another batch."
                    )

        current_user_id = current_user.id if current_user else None

        try:
            batch_repository.update_batch(
                db=self.db,
                batch=batch,
                batch_data=batch_data,
                updated_by=current_user_id,
                commit=False,
            )

            if batch_data.batch_users is not None and employee_role:
                self._sync_batch_users(
                    batch=batch,
                    requested_user_ids=batch_data.batch_users,
                    employee_role=employee_role,
                    current_user=current_user,
                )

            if batch_data.batch_admins is not None and batch_admin_role:
                self._sync_batch_admins(
                    batch=batch,
                    requested_user_ids=batch_data.batch_admins,
                    batch_admin_role=batch_admin_role,
                    current_user=current_user,
                )

            self.db.commit()
            self.db.refresh(batch)
            users, admins = self._get_batch_members_lists(batch.id)
            batch.users = users
            batch.admins = admins
            return batch
        except Exception:
            self.db.rollback()
            raise


    def delete_batch(
        self,
        batch_id: UUID,
        current_user,
    ) -> Batch:

        batch = batch_repository.get_batch_by_id(
            db=self.db,
            batch_id=batch_id,
        )

        if not batch:
            raise BatchNotFoundException(
                "Batch not found."
            )

        self._validate_batch_tenant_access(
            current_user=current_user,
            organization_id=batch.organization_id,
            batch_id=batch.id,
            action="delete",
        )

        self.validate_batch_open(batch)

        deleted_by = getattr(current_user, "id", None) if current_user else None
        return batch_repository.soft_delete_batch(
            db=self.db,
            batch=batch,
            deleted_by=deleted_by,
        )

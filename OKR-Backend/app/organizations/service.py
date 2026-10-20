import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

UPLOAD_DIR = os.path.join("uploads", "logos")
BASE_DIR = Path(__file__).resolve().parent.parent.parent
from app.common.exceptions import (
    ForbiddenException,
    OrganizationAlreadyExistsException,
    OrganizationNotFoundException,
)
from app.organization_members.models import OrganizationMember
from app.rbac.dependencies import is_super_admin
from app.users.models import User

from app.organizations import repository
from app.organizations.models import Organization
from app.organizations.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
)


def create_organization_service(
    db: Session,
    organization_data: OrganizationCreate,
    logo: UploadFile | None = None,
    current_user_id=None,
):
    """
    Create organization.

    Business Rules:
    - Organization name must be unique
    """

    existing_name = repository.get_organization_by_name(
        db,
        organization_data.name,
    )

    if existing_name:
        raise OrganizationAlreadyExistsException(
            "Organization name already exists"
        )

    logo_path = None

    if logo:
        # Validate
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        if logo.content_type not in allowed_types:
            raise ValueError("Invalid logo format")

        # Generate filename
        extension = Path(logo.filename).suffix.lower()

        filename = f"{uuid.uuid4()}{extension}"

        # Save location
        upload_dir = BASE_DIR / "uploads" / "logo"
        upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = upload_dir / filename

        with open(file_path, "wb") as buffer:
            buffer.write(logo.file.read())

        # Store relative path
        logo_path = f"uploads/logo/{filename}"

    organization = Organization(
        name=organization_data.name,
        description=organization_data.description,
        logo=logo_path,
        website=str(organization_data.website)
        if organization_data.website
        else None,
        email=organization_data.email,
        phone=organization_data.phone,
        address=organization_data.address,
        created_by=current_user_id,
        updated_by=current_user_id,
    )

    return repository.create_organization(
        db,
        organization,
    )


def _validate_org_access(db: Session, current_user: User | None, organization_id) -> None:
    if not current_user or is_super_admin(current_user, db=db):
        return

    caller_memberships = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.is_deleted.is_(False),
            OrganizationMember.is_active.is_(True),
        )
        .all()
    )
    allowed_org_ids = {m.organization_id for m in caller_memberships if m.organization_id is not None}
    if organization_id not in allowed_org_ids:
        raise ForbiddenException("Access denied to this organization.")


def list_organizations_service(
    db: Session,
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    current_user: User | None = None,
):
    """
    List organizations with pagination, search, filters, and sorting.
    Non-superadmins are strictly scoped to the organizations they belong to.
    """
    organization_ids = None

    if current_user and not is_super_admin(current_user, db=db):
        caller_memberships = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.is_deleted.is_(False),
                OrganizationMember.is_active.is_(True),
            )
            .all()
        )
        allowed_org_ids = [m.organization_id for m in caller_memberships if m.organization_id is not None]
        organization_ids = allowed_org_ids

    skip = (page - 1) * size

    get_kwargs = {
        "skip": skip,
        "limit": size,
        "search": search,
        "is_active": is_active,
    }
    count_kwargs = {
        "search": search,
        "is_active": is_active,
    }

    if organization_ids is not None:
        get_kwargs["organization_ids"] = organization_ids
        count_kwargs["organization_ids"] = organization_ids

    if sort_by is not None:
        get_kwargs["sort_by"] = sort_by
    if sort_order is not None:
        get_kwargs["sort_order"] = sort_order
    if created_after is not None:
        get_kwargs["created_after"] = created_after
        count_kwargs["created_after"] = created_after
    if created_before is not None:
        get_kwargs["created_before"] = created_before
        count_kwargs["created_before"] = created_before

    organizations = repository.get_organizations(
        db,
        **get_kwargs,
    )

    total = repository.count_organizations(
        db,
        **count_kwargs,
    )

    total_pages = (total + size - 1) // size if total > 0 else 1

    return {
        "data": organizations,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def get_organization_service(
    db: Session,
    organization_id,
    current_user: User | None = None,
):
    """
    Get organization details.
    """
    _validate_org_access(db=db, current_user=current_user, organization_id=organization_id)

    organization = repository.get_organization_by_id(
        db,
        organization_id,
    )

    if not organization:
        raise OrganizationNotFoundException(
            "Organization not found"
        )

    return organization


def update_organization_service(
    db: Session,
    organization_id,
    organization_data: OrganizationUpdate,
    current_user_id=None,
    current_user: User | None = None,
):
    """
    Update organization.

    Business Rules:
    - Organization must exist
    - Organization name must be unique
    """
    _validate_org_access(db=db, current_user=current_user, organization_id=organization_id)

    organization = repository.get_organization_by_id(
        db,
        organization_id,
    )

    if not organization:
        raise OrganizationNotFoundException(
            "Organization not found"
        )

    if organization_data.name:

        existing_name = repository.get_organization_by_name(
            db,
            organization_data.name,
        )

        if (
            existing_name
            and existing_name.id != organization.id
        ):
            raise OrganizationAlreadyExistsException(
                "Organization name already exists"
            )

        organization.name = organization_data.name

    if organization_data.description is not None:
        organization.description = (
            organization_data.description
        )

    if organization_data.logo is not None:
        organization.logo = (
            organization_data.logo
        )

    if organization_data.website is not None:
        organization.website = str(
            organization_data.website
        )

    if organization_data.email is not None:
        organization.email = (
            organization_data.email
        )

    if organization_data.phone is not None:
        organization.phone = (
            organization_data.phone
        )

    if organization_data.address is not None:
        organization.address = (
            organization_data.address
        )

    if organization_data.is_active is not None:
        organization.is_active = (
            organization_data.is_active
        )

    organization.updated_by = current_user_id

    return repository.update_organization(
        db,
        organization,
    )


def delete_organization_service(
    db: Session,
    organization_id,
    current_user_id=None,
):
    """
    Soft delete organization.

    Rules:
    - Do not physically delete
    - Mark organization inactive
    """

    organization = repository.get_organization_by_id(
        db,
        organization_id,
    )

    if not organization:
        raise OrganizationNotFoundException(
            "Organization not found"
        )

    organization.is_deleted = True
    organization.is_active = False
    organization.deleted_at = datetime.now(timezone.utc)
    organization.updated_by = current_user_id

    return repository.delete_organization(
        db,
        organization,
    )


def upload_organization_logo_service(
    db: Session,
    organization_id,
    file: UploadFile,
    current_user_id=None,
    current_user: User | None = None,
):
    """
    Upload and save organization logo image file.

    - Validates organization existence
    - Creates upload directory uploads/logos/ if missing
    - Saves file with a unique filename
    - Updates database column logo with relative path /uploads/logos/<filename>
    """
    _validate_org_access(db=db, current_user=current_user, organization_id=organization_id)

    organization = repository.get_organization_by_id(
        db,
        organization_id,
    )

    if not organization:
        raise OrganizationNotFoundException(
            "Organization not found"
        )

    # Ensure uploads/logos directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Extract file extension
    original_filename = file.filename or "logo.png"
    file_ext = os.path.splitext(original_filename)[1]
    if not file_ext:
        file_ext = ".png"

    # Create unique filename
    unique_filename = f"{organization_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Write file content to disk
    file_bytes = file.file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    # Store relative web URL path in database
    relative_path = f"/uploads/logos/{unique_filename}"
    organization.logo = relative_path
    organization.updated_by = current_user_id
    organization.updated_at = datetime.now(timezone.utc)

    return repository.update_organization(
        db,
        organization,
    )


from datetime import datetime
from uuid import UUID
from fastapi import Form, UploadFile
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.organizations.schemas import (
    OrganizationCreate,
    OrganizationPaginatedResponse,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.organizations.service import (
    create_organization_service,
    delete_organization_service,
    get_organization_service,
    list_organizations_service,
    update_organization_service,
    upload_organization_logo_service,
)
from app.rbac.dependencies import require_permission
from app.users.models import User

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
    dependencies=[
        Depends(get_current_user)
    ],
)


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=201,
)
def create_organization(
    name: str = Form(...),
    description: str | None = Form(None),
    website: str | None = Form(None),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    address: str | None = Form(None),

    logo: UploadFile | None = File(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_permission("organization.create")
    ),
):
    """
    Create organization.
    """
    organization_data = OrganizationCreate(
    name=name,
    description=description,
    website=website,
    email=email,
    phone=phone,
    address=address,
)

    return create_organization_service(
        db=db,
        organization_data=organization_data,
        logo=logo,
        current_user_id=current_user.id,
    )


@router.get(
    "/",
    response_model=OrganizationPaginatedResponse,
)
def list_organizations(
    page: int = Query(
        1,
        ge=1,
    ),
    size: int = Query(
        10,
        ge=1,
        le=100,
    ),
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str | None = Query(default="created_at"),
    sort_order: str | None = Query(default="desc"),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("organization.view")),
):
    """
    List organizations with pagination, search, active filtering, and sorting.
    """

    return list_organizations_service(
        db=db,
        page=page,
        size=size,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
        created_after=created_after,
        created_before=created_before,
        current_user=current_user,
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def get_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("organization.view")),
):
    """
    Get organization details.
    """

    return get_organization_service(
        db=db,
        organization_id=organization_id,
        current_user=current_user,
    )


@router.put(
    "/{organization_id}",
    response_model=OrganizationResponse,
)
def update_organization(
    organization_id: UUID,
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("organization.update")),
):
    """
    Update organization.
    """

    return update_organization_service(
        db=db,
        organization_id=organization_id,
        organization_data=data,
        current_user_id=current_user.id,
        current_user=current_user,
    )


@router.delete(
    "/{organization_id}",
)
def delete_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("organization.delete")),
):
    """
    Soft delete organization.
    """

    delete_organization_service(
        db=db,
        organization_id=organization_id,
        current_user_id=current_user.id,
    )

    return {
        "success": True,
        "message": "Organization deleted successfully.",
    }


@router.post(
    "/{organization_id}/logo",
    response_model=OrganizationResponse,
)
def upload_organization_logo(
    organization_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("organization.update")),
):
    """
    Upload organization logo image file.
    """
    return upload_organization_logo_service(
        db=db,
        organization_id=organization_id,
        file=file,
        current_user_id=current_user.id,
        current_user=current_user,
    )


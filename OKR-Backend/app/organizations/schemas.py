from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl


class OrganizationCreate(BaseModel):
    """
    Schema for creating a new organization.
    """

    name: str

    description: str | None = None

    website: HttpUrl | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None


class OrganizationUpdate(BaseModel):
    """
    Schema for updating an existing organization.
    """

    name: str | None = None
    description: str | None = None
    logo: str | None = None
    website: HttpUrl | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool | None = None


class OrganizationResponse(BaseModel):
    """
    Schema for returning full organization details.
    """

    id: UUID

    name: str

    description: str | None = None
    logo: str | None = None
    website: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

    is_active: bool = True
    is_deleted: bool = False

    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


class OrganizationListResponse(BaseModel):
    """
    Response schema for organization listing including contact details.
    """

    id: UUID
    name: str

    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    is_active: bool = True

    model_config = ConfigDict(
        from_attributes=True
    )


class Pagination(BaseModel):
    """
    Pagination metadata model.
    """

    page: int
    size: int
    total: int


class OrganizationPaginatedResponse(BaseModel):
    """
    Paginated response schema for list_organizations API with full details.
    """

    data: list[OrganizationResponse]
    pagination: Pagination

    model_config = ConfigDict(
        from_attributes=True
    )



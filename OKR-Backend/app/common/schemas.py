"""
Common Pydantic schemas shared across modules.

Contains:
- API response wrappers
- Pagination schemas
- Common error structures
"""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class AuditSchemaMixin(BaseModel):
    """
    Common audit fields mixin for schemas.
    """

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    is_active: bool = True
    is_deleted: bool = False


# =====================================================
# Pagination
# =====================================================


class PaginationResponse(BaseModel):
    """
    Pagination metadata for list APIs.
    """

    page: int
    size: int
    total: int
    total_pages: int | None = None
    has_next: bool | None = None
    has_prev: bool | None = None



# =====================================================
# Error Schema
# =====================================================


class ErrorDetail(BaseModel):
    """
    Individual validation/business error.
    """

    field: str | None = None

    message: str


class ErrorResponse(BaseModel):
    """
    Standard API error response.
    """

    success: bool = False

    message: str

    errors: list[ErrorDetail] = []


# =====================================================
# Success Response
# =====================================================


class ResponseSchema(
    BaseModel,
    Generic[T],
):
    """
    Standard API success response.

    Example:

    {
        "success": true,
        "message": "User created successfully",
        "data": {}
    }
    """

    success: bool = True

    message: str

    data: T | None = None

    pagination: PaginationResponse | None = None

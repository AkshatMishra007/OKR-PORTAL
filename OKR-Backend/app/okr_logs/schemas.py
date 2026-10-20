"""
Pydantic schemas for OKR Logs module.
"""
from datetime import datetime as dt
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.common.schemas import AuditSchemaMixin


class OkrLogBase(BaseModel):
    """Base schema for OKR log."""
    weekly_no: int
    current_user: UUID
    datetime: dt | None = None


class OkrLogCreate(OkrLogBase):
    """Schema for creating an OKR log."""
    pass


class OkrLogResponse(AuditSchemaMixin):
    """Response schema for OKR log including audit attributes."""
    weekly_no: int
    current_user: UUID
    datetime: dt

    model_config = ConfigDict(from_attributes=True)

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID


class UUIDMixin:
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


class AuditModel:
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )


class SoftDeleteModel:
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    deleted_at = Column(
        DateTime,
        nullable=True,
    )


class BaseModel(
    UUIDMixin,
    AuditModel,
    SoftDeleteModel,
):
    """
    Common fields shared by all models.
    """

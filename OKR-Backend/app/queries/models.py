from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base


# ==========================================================
# Enums
# ==========================================================


class QueryPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class QueryStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


# ==========================================================
# Query Model
# ==========================================================


class Query(Base, BaseModel):
    __tablename__ = "queries"

    ticket_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    subject = Column(
        String(255),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    priority = Column(
        SQLEnum(
            QueryPriority,
            name="query_priority",
        ),
        default=QueryPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    status = Column(
        SQLEnum(
            QueryStatus,
            name="query_status",
        ),
        default=QueryStatus.OPEN,
        nullable=False,
        index=True,
    )

    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    assigned_at = Column(
        DateTime,
        nullable=True,
    )

    resolution_note = Column(
        Text,
        nullable=True,
    )

    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    resolved_at = Column(
        DateTime,
        nullable=True,
    )

    closed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    closed_at = Column(
        DateTime,
        nullable=True,
    )

    submitted_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # ======================================================
    # Relationships
    # ======================================================

    raised_by = relationship(
        "User",
        foreign_keys=[user_id],
    )

    assigned_user = relationship(
        "User",
        foreign_keys=[assigned_to],
    )

    resolved_user = relationship(
        "User",
        foreign_keys=[resolved_by],
    )

    closed_user = relationship(
        "User",
        foreign_keys=[closed_by],
    )

    activities = relationship(
        "QueryActivity",
        back_populates="query",
        cascade="all, delete-orphan",
    )
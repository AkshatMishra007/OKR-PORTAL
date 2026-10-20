# app/models/okr.py

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base
from app.fogs_hurdles.models import FogsHurdle
import app.weekly_update.models  # noqa: F401
import app.tracker_entries.models  # noqa: F401


class OKR(BaseModel, Base):
    __tablename__ = "okrs"

    batch_id = Column(
    UUID(as_uuid=True),
    ForeignKey("batches.id"),
    nullable=False,
    index=True,
    )

    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("organization_members.id"),
        nullable=False,
        index=True,
    )

    objective = Column(
        Text,
        nullable=False,
    )

    target = Column(
        String(255),
        nullable=True,
    )

    key_results = Column(
        Text,
        nullable=True,
        default="",
    )

    okr_type = Column(
        String(20),
        nullable=False,
    )

    tracker_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    # Relationships

    batch = relationship(
    "Batch",
    back_populates="okrs",
    )

    assignee = relationship(
        "OrganizationMember",
        back_populates="okrs",
        foreign_keys=[assigned_to],
    )

    weekly_updates = relationship(
        "WeeklyUpdate",
        back_populates="okr",
    )

    tracker_entries = relationship(
        "TrackerEntry",
        back_populates="okr",
    )

    fogs_hurdles = relationship(
        "FogsHurdle",
        back_populates = "okr",
    )

    @property
    def organization(self):
        """Eagerly loaded Organization entity via Batch or OrganizationMember."""
        if self.batch and hasattr(self.batch, "organization") and self.batch.organization:
            return self.batch.organization
        if self.assignee and hasattr(self.assignee, "organization") and self.assignee.organization:
            return self.assignee.organization
        return None

    @property
    def organization_id(self):
        """Organization UUID via Batch or OrganizationMember."""
        if self.batch and hasattr(self.batch, "organization_id") and self.batch.organization_id:
            return self.batch.organization_id
        if self.assignee and hasattr(self.assignee, "organization_id") and self.assignee.organization_id:
            return self.assignee.organization_id
        return None

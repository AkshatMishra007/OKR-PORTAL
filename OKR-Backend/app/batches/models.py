from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base


class BatchStatus(str, PyEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class Quarter(str, PyEnum):
    JFM = "JFM"  # January - February - March
    AMJ = "AMJ"  # April - May - June
    JAS = "JAS"  # July - August - September
    OND = "OND"  # October - November - December


class MeetingDay(str, PyEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


class Batch(Base, BaseModel):

    __tablename__ = "batches"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            "year",
            "quarter",
            name="uq_batch_org_name_year_quarter",
        ),
    )

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    year = Column(
        Integer,
        nullable=False,
        index=True,
    )

    quarter = Column(
        Enum(
            Quarter,
            name="batch_quarter_enum",
        ),
        nullable=False,
    )

    start_date = Column(
        Date,
        nullable=False,
    )

    end_date = Column(
        Date,
        nullable=False,
    )

    meeting_day = Column(
        Enum(
            MeetingDay,
            name="meeting_day_enum",
        ),
        nullable=False,
    )

    status = Column(
        Enum(
            BatchStatus,
            name="batch_status_enum",
        ),
        nullable=False,
        default=BatchStatus.DRAFT,
    )

    closed_at = Column(
        DateTime,
        nullable=True,
    )

    closed_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    organization = relationship(
        "Organization",
        back_populates="batches",
    )

    batch_members = relationship(
        "BatchMember",
        back_populates="batch",
    )

    okrs = relationship(
        "OKR",
        back_populates="batch",
    )


class BatchMember(Base, BaseModel):
    __tablename__ = "batch_members"

    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "user_id",
            name="uq_batch_member_batch_user",
        ),
    )

    batch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batches.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
        index=True,
    )

    batch = relationship(
        "Batch",
        back_populates="batch_members",
    )

    user = relationship(
        "User",
        back_populates="batch_members",
    )

    role = relationship(
        "Role",
        back_populates="batch_members",
    )
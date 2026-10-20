from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base


class WeeklyUpdate(Base, BaseModel):
    __tablename__ = "weekly_updates"

    __table_args__ = (
        # UniqueConstraint(
        #     "okr_id",
        #     "week_number",
        #     name="uq_weekly_update_okr_week",
        # ),
        # CheckConstraint(
        #     "progress >= 0 AND progress <= 100",
        #     name="ck_weekly_update_progress",
        # ),
    )

    okr_id = Column(
        UUID(as_uuid=True),
        ForeignKey("okrs.id"),
        nullable=False,
        index=True,
    )

    week_number = Column(
        Integer,
        nullable=False,
    )

    progress = Column(
        Integer,
        nullable=False,
    )

    remarks = Column(
        Text,
        nullable=True,
    )

    okr = relationship(
        "OKR",
        back_populates="weekly_updates",
    )
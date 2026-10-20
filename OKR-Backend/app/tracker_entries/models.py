from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base


class TrackerEntry(Base, BaseModel):
    __tablename__ = "tracker_entries"

    __table_args__ = (
        # UniqueConstraint(
        #     "okr_id",
        #     "week_start",
        #     name="uq_tracker_entry_okr_week",
        # ),
        CheckConstraint(
            "opportunities_received >= 0",
            name="ck_tracker_opportunities_received",
        ),
        CheckConstraint(
            "opportunities_completed >= 0",
            name="ck_tracker_opportunities_completed",
        ),
    )

    okr_id = Column(
        UUID(as_uuid=True),
        ForeignKey("okrs.id"),
        nullable=False,
        index=True,
    )

    week_start = Column(
        Date,
        nullable=False,
    )

    opportunities_received = Column(
        Integer,
        nullable=False,
        default=0,
    )

    opportunities_completed = Column(
        Integer,
        nullable=False,
        default=0,
    )

    okr = relationship(
        "OKR",
        back_populates="tracker_entries",
    )

    @property
    def target(self) -> str | None:
        """
        Derive target from the associated OKR model.
        """
        return self.okr.target if self.okr else None

    @property
    def weekly_completion_efficiency(self) -> float:
        """
        Calculate weekly completion efficiency percentage.
        Returns 0.0 if opportunities_received is 0.
        """
        if not self.opportunities_received or self.opportunities_received <= 0:
            return 0.0
        return round((self.opportunities_completed / self.opportunities_received) * 100.0, 2)
from datetime import UTC, datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base


class OkrLog(Base, BaseModel):
    __tablename__ = "okr_logs"

    weekly_no = Column(
        Integer,
        nullable=False,
    )

    current_user = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    datetime = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship(
        "User",
        foreign_keys=[current_user],
    )

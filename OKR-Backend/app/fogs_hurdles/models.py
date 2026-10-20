from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base


class FogsHurdle(Base, BaseModel):
    __tablename__ = "fogs_hurdles"

    okr_id = Column(
        UUID(as_uuid=True),
        ForeignKey("okrs.id"),
        nullable=False,
        index=True,
    )

    fogs_hurdles = Column(
        Text,
        nullable=False,
    )

    action_points = Column(
        Text,
        nullable=True,
    )

    # relationships

    okr = relationship(
        "OKR",
        back_populates="fogs_hurdles",
    )
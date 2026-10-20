from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.common.models import BaseModel


class Role(Base, BaseModel):
    __tablename__ = "roles"

    name = Column(
        String(100),
        nullable=False,
    )


    description = Column(
        Text,
        nullable=True,
    )

    organization_members = relationship(
        "OrganizationMember",
        back_populates="role",
    )
    batch_members = relationship(
        "BatchMember",
        back_populates="role",
    )
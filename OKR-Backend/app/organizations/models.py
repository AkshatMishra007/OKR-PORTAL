from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base
import app.organization_members.models  # noqa: F401
import app.batches.models  # noqa: F401


class Organization(Base, BaseModel):

    __tablename__ = "organizations"

    name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )


    description = Column(
        Text,
        nullable=True,
    )

    logo = Column(
        String(500),
        nullable=True,
    )

    website = Column(
        String(255),
        nullable=True,
    )

    email = Column(
        String(255),
        nullable=True,
    )

    phone = Column(
        String(30),
        nullable=True,
    )

    address = Column(
        Text,
        nullable=True,
    )


    organization_members = relationship(
        "OrganizationMember",
        back_populates="organization",
    )


    batches = relationship(
        "Batch",
        back_populates="organization",
    )
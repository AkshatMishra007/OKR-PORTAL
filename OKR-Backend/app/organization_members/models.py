from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.core.database import Base


class OrganizationMember(Base, BaseModel):
    __tablename__ = "organization_members"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
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
    )

    joined_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    organization = relationship(
        "Organization",
        back_populates="organization_members",
    )

    user = relationship(
        "User",
        back_populates="organization_members",
    )

    role = relationship(
        "Role",
        back_populates="organization_members",
    )

    okrs = relationship(
        "OKR",
        back_populates="assignee",
    )

    @property
    def organization_name(self) -> str:
        if hasattr(self, "organization") and self.organization:
            return self.organization.name
        return ""
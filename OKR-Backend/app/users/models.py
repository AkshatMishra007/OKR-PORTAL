from sqlalchemy import Column, DateTime, String, Text,Index
from app.common.models import BaseModel
from app.core.database import Base
from sqlalchemy.orm import relationship

class User(Base, BaseModel):
    __tablename__ = "users"

    username = Column(
        String(100),
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=False,
    )


    password_hash = Column(
        String,
        nullable=False,
    )

    first_name = Column(
        String(100),
        nullable=False,
    )

    last_name = Column(
        String(100),
        nullable=True,
    )

    phone = Column(
        String(20),
        nullable=True,
    )

    designation = Column(
        String(100),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    last_login = Column(
        DateTime,
        nullable=True,
    )
    organization_members = relationship(
        "OrganizationMember",
        back_populates="user",
    )
    batch_members = relationship(
        "BatchMember",
        back_populates="user",
    )

    @property
    def name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name

    @property
    def role(self):
        if hasattr(self, "_role"):
            return self._role
        if hasattr(self, "organization_members") and self.organization_members:
            for member in self.organization_members:
                if not getattr(member, "is_deleted", False) and getattr(member, "role", None):
                    return member.role
        return None

    @role.setter
    def role(self, value):
        self._role = value

    @property
    def organization_memberships(self) -> list:
        if hasattr(self, "organization_members") and self.organization_members:
            active_memberships = [
                m for m in self.organization_members
                if not getattr(m, "is_deleted", False) and getattr(m, "is_active", True)
            ]
            unique_by_org = {}
            for m in sorted(
                active_memberships,
                key=lambda x: (getattr(x, "joined_at", None) or getattr(x, "created_at", None)),
                reverse=True,
            ):
                if m.organization_id not in unique_by_org:
                    unique_by_org[m.organization_id] = m
            return list(unique_by_org.values())
        return []

    
Index(
            "uq_users_username_active",
        "username",
        unique=True,
        postgresql_where=(User.is_deleted == False),
    ),
Index(
            "uq_users_email_active",
        "email",
        unique=True,
        postgresql_where=(User.is_deleted == False),
    ),
    
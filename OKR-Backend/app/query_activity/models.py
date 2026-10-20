from enum import Enum
from sqlalchemy import (
    Column,
    Enum as SQLEnum,
    String,
    ForeignKey,
    Text
)
from sqlalchemy.dialects.postgresql import UUID 
from sqlalchemy.orm import relationship
from app.common.models import BaseModel
from app.core.database import Base

# ==========================================================
# Activity Type Enum
# ==========================================================

class QueryActivityType(str,Enum):
    CREATED="CREATED"
    ASSIGNED="ASSIGNED"
    STATUS_UPDATED="STATUS_UPDATED"
    RESOLVED="RESOLVED"
    CLOSED="CLOSED"

# ==========================================================
# Query Activity Model
# ==========================================================
class QueryActivity(Base, BaseModel):
    __tablename__="query_activity"
    query_id=Column(
        UUID(as_uuid=True),
        ForeignKey("queries.id"),
        nullable=False,
        index=True,
    )
    activity_type=Column(
        SQLEnum(
            QueryActivityType,
            name="query_activity_type"
        ),
        nullable=False
    )
    description=Column(
        Text,
        nullable=False
    )
    performed_by=Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
   # ======================================================
    # Relationships
    # ======================================================
    query=relationship(
        "Query",
        back_populates="activities"
    )
    performed_user=relationship(
        "User",
        foreign_keys=[performed_by],
    )
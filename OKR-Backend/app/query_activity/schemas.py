from datetime import datetime
from uuid import UUID
from pydantic import BaseModel,ConfigDict
from app.query_activity.models import QueryActivityType


# ==========================================================
# Query Activity Response
# ==========================================================

class QueryActivityResponse(BaseModel):
    """
    Schema for query activity response.
    """
    id:UUID
    query_id:UUID
    activity_type:QueryActivityType
    description:str
    performed_by:UUID
    created_at:datetime
    model_config=ConfigDict(
        from_attributes=True,
    )
 
# ==========================================================
# Query Activity List Response
# ==========================================================

class QueryActivityListResponse(BaseModel):
    """
    Schema for query activity listing.
    """
    activities: list[QueryActivityResponse]
    total: int | None = None
    page: int | None = None
    size: int | None = None
    model_config = ConfigDict(
        from_attributes=True,
    )
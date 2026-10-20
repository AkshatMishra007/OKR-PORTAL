"""
Query Pydantic schemas.

Responsibilities:
- Validate incoming query data.
- Define API response formats.
- Hide internal database fields.
"""
from dns import message
from datetime import datetime 
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field,computed_field
from app.queries.models import QueryPriority,QueryStatus
from typing import List
from typing import Dict


class QueryCreate(BaseModel):
    subject:str=Field(
        min_length=5,
        max_length=255
    )
    message:str=Field(
        min_length=10
    )
    priority:QueryPriority=QueryPriority.MEDIUM


class QueryResponse(BaseModel):
    id:UUID
    ticket_number:str
    user_id:UUID
    subject:str
    message:str
    priority:QueryPriority
    status: QueryStatus
    submitted_at:datetime
    assigned_to:UUID|None
    resolution_note:str|None=None
    resolved_by:UUID|None
    closed_by:UUID|None
    resolved_at:datetime|None
    closed_at:datetime|None


    @computed_field
    @property
    def resolution_time(self)-> int |None:
        """
        Calculate resolution time in seconds
        """
        if not self.resolved_at:
            return None
        return int (
         (self.resolved_at-self.submitted_at).total_seconds()
        )

    @computed_field
    @property
    def closure_time(self)->int |None:
        """
        Calculate closure time in seconds
        """
        if not self.closed_at:
            return None
        return int (
         (self.closed_at-self.submitted_at).total_seconds()
        )


    model_config = ConfigDict(
        from_attributes=True
    )

class QueryAssignment(BaseModel):
    """
    Schema for assigning a query to an agent.
    """

    assigned_to: UUID


# ==========================================================
# Query Listing Filters
# ==========================================================

class QueryListFilters(BaseModel):
    """
    Query Listing Filters
    """

    page:int=Field(default=1,ge=1)
    page_size:int=Field(default=10,ge=1,le=100)
    search:str|None=None
    status:QueryStatus|None=None
    priority:QueryPriority|None=None
    sort_by:str="submitted_at"
    sort_order:str="desc"

# ==========================================================
# Query Listing Response
# ==========================================================

class QueryListResponse(BaseModel):
    """
    Paginated query list response
    """
    items:List[QueryResponse]
    total:int
    page:int
    page_size:int
    total_pages:int
    model_config=ConfigDict(
        from_attributes=True
    )
# ==========================================================
# Query Status Update
# ==========================================================


class QueryStatusUpdate(BaseModel):
    """
    Schema for updating query status.
    """

    status: QueryStatus

# ==========================================================
# Query Resolution
# ==========================================================


class QueryResolve(BaseModel):
    """
    Schema for resolving a query.
    """

    resolution_note: str
# ==========================================================
# Query Dashboard & Analytics
# ==========================================================


class QueryStatusAnalytics(BaseModel):
    OPEN: int = 0
    IN_PROGRESS: int = 0
    RESOLVED: int = 0
    CLOSED: int = 0
    REOPENED: int = 0


class QueryPriorityAnalytics(BaseModel):
    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    URGENT: int = 0


class QueryDashboardResponse(BaseModel):
    """
    Query dashboard and analytics response.
    """

    total_queries: int

    status_counts: QueryStatusAnalytics

    priority_counts: QueryPriorityAnalytics

    average_resolution_time: int | None = None

    average_closure_time: int | None = None
from sqlalchemy.orm import Session
from app.query_activity.models import QueryActivity

# ==========================================================
# Create Activity
# ==========================================================

def create_activity(
    db:Session,
    activity:QueryActivity,
):
    """
    Create a query activity
    """
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# ==========================================================
# Get Query Activities
# ==========================================================

from app.common.query import validate_and_apply_sorting, paginate_query

ALLOWED_ACTIVITY_SORT_FIELDS = {
    "created_at": QueryActivity.created_at,
    "activity_type": QueryActivity.activity_type,
}


def get_query_activities(
    db: Session,
    query_id,
    page: int = 1,
    size: int = 20,
    activity_type = None,
    sort_by: str | None = "created_at",
    sort_order: str | None = "asc",
):
    """
    Get query history for a query with optional filtering, sorting, and pagination.
    """
    query = db.query(QueryActivity).filter(
        QueryActivity.query_id == query_id,
        QueryActivity.is_deleted.is_(False),
    )

    if activity_type:
        query = query.filter(QueryActivity.activity_type == activity_type)

    query = validate_and_apply_sorting(
        query=query,
        model=QueryActivity,
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_sort_fields=ALLOWED_ACTIVITY_SORT_FIELDS,
        default_sort_column=QueryActivity.created_at,
    )

    items, meta = paginate_query(query=query, page=page, size=size)
    return list(items), meta["total"]
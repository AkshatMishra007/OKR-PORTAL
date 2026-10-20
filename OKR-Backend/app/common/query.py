"""
Common query builder utilities for Filtering, Sorting, and Pagination.
"""

from math import ceil
from typing import Any, Sequence, TypeVar
from sqlalchemy import asc, desc
from sqlalchemy.orm import Query as ORMQuery

T = TypeVar("T")


def validate_and_apply_sorting(
    query: ORMQuery,
    model: Any,
    sort_by: str | None = None,
    sort_order: str | None = "desc",
    allowed_sort_fields: dict[str, Any] | None = None,
    default_sort_column: Any | None = None,
) -> ORMQuery:
    """
    Safely apply sorting to an ORM Query.

    - Whitelists sortable fields against `allowed_sort_fields` or model attributes.
    - Applies `asc` or `desc` order.
    - Appends deterministic secondary sorting by `model.id` if available.
    """
    if allowed_sort_fields is None:
        allowed_sort_fields = {}

    target_column = None

    if sort_by and sort_by in allowed_sort_fields:
        target_column = allowed_sort_fields[sort_by]
    elif sort_by and hasattr(model, sort_by):
        col = getattr(model, sort_by)
        # Ensure it's an ORM column / attribute and not a method
        if hasattr(col, "asc") and hasattr(col, "desc"):
            target_column = col

    if target_column is None:
        if default_sort_column is not None:
            target_column = default_sort_column
        elif hasattr(model, "created_at"):
            target_column = getattr(model, "created_at")
        elif hasattr(model, "id"):
            target_column = getattr(model, "id")

    if target_column is not None:
        order_fn = asc if sort_order and sort_order.lower() == "asc" else desc
        query = query.order_by(order_fn(target_column))

    # Secondary deterministic sorting by primary key ID if available
    if hasattr(model, "id") and target_column is not getattr(model, "id", None):
        order_fn = asc if sort_order and sort_order.lower() == "asc" else desc
        query = query.order_by(order_fn(getattr(model, "id")))

    return query


def paginate_query(
    query: ORMQuery,
    page: int = 1,
    size: int = 20,
    max_size: int = 100,
) -> tuple[Sequence[Any], dict[str, Any]]:
    """
    Perform DB pagination on a query and construct pagination metadata.
    """
    # Sanitize pagination parameters
    page = max(1, page)
    size = max(1, min(size, max_size))

    total = query.count()
    total_pages = ceil(total / size) if total > 0 else 1

    # Clamp page to maximum total pages if out of bounds and total > 0
    if page > total_pages and total > 0:
        page = total_pages

    skip = (page - 1) * size
    items = query.offset(skip).limit(size).all()

    pagination = {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    return items, pagination

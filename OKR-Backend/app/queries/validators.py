from app.common.exceptions import BadRequestException
from app.queries.models import QueryStatus


ALLOWED_STATUS_TRANSITIONS = {
    QueryStatus.OPEN: {
        QueryStatus.IN_PROGRESS,
    },
    QueryStatus.IN_PROGRESS: {
        QueryStatus.RESOLVED,
    },
    QueryStatus.RESOLVED: {
        QueryStatus.CLOSED,
        QueryStatus.REOPENED,
    },
    QueryStatus.CLOSED: {
        QueryStatus.REOPENED,
    },
    QueryStatus.REOPENED: {
        QueryStatus.IN_PROGRESS,
    },
}


def validate_status_transition(
    current_status: QueryStatus,
    new_status: QueryStatus,
) -> None:
    """
    Validate whether a query can move from its
    current status to the requested status.
    """

    if current_status == new_status:
        raise BadRequestException(
            f"Query is already in {current_status.value} status."
        )

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise BadRequestException(
            f"Invalid status transition: "
            f"{current_status.value} -> {new_status.value}."
        )

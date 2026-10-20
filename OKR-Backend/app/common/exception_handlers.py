from fastapi import Request
from fastapi.responses import JSONResponse

from app.common.exceptions import (
    AppException,
    ForbiddenException,
    InvalidCredentialsException,
    OrganizationMemberNotFoundException,
    OrganizationNotFoundException,
    RoleNotFoundException,
    UnauthorizedException,
    UserNotFoundException,
    BatchNotFoundException,
    BatchMemberNotFoundException,
    OKRNotFoundException,
    WeeklyUpdateNotFoundException,
    TrackerEntryNotFoundException,
    FogsHurdleNotFoundException,
)


def app_exception_handler(
    request: Request,
    exc: AppException,
):
    if isinstance(
        exc,
        (
            InvalidCredentialsException,
            UnauthorizedException,
        ),
    ):
        status_code = 401

    elif isinstance(
        exc,
        ForbiddenException,
    ):
        status_code = 403

    elif isinstance(
        exc,
        (
            UserNotFoundException,
            OrganizationNotFoundException,
            RoleNotFoundException,
            OrganizationMemberNotFoundException,
            BatchNotFoundException,
            BatchMemberNotFoundException,
            OKRNotFoundException,
            WeeklyUpdateNotFoundException,
            TrackerEntryNotFoundException,
            FogsHurdleNotFoundException,
        ),
    ):
        status_code = 404

    else:
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": exc.message,
        },
    )
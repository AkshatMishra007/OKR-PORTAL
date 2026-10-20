
from app.common.exception_handlers import app_exception_handler
from app.common.exceptions import (
    AppException,
    ForbiddenException,
    InvalidCredentialsException,
    UnauthorizedException,
    UserNotFoundException,
)


def test_exception_handler_invalid_credentials():
    response = app_exception_handler(None, InvalidCredentialsException("Invalid creds"))
    assert response.status_code == 401


def test_exception_handler_unauthorized():
    response = app_exception_handler(None, UnauthorizedException("Unauthorized"))
    assert response.status_code == 401


def test_exception_handler_forbidden():
    response = app_exception_handler(None, ForbiddenException("Forbidden access"))
    assert response.status_code == 403


def test_exception_handler_user_not_found():
    response = app_exception_handler(None, UserNotFoundException("User missing"))
    assert response.status_code == 404


def test_exception_handler_generic_app_exception():
    response = app_exception_handler(None, AppException("Generic app error"))
    assert response.status_code == 400

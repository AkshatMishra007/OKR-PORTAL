"""
Application level exceptions.

Services raise these exceptions.
API layer converts them into HTTP responses.
"""


class AppException(Exception):
    """
    Base application exception.
    """

    def __init__(
        self,
        message: str,
    ):
        self.message = message

        super().__init__(message)


# =====================================================
# Common HTTP Exceptions
# =====================================================


class BadRequestException(AppException):
    """
    Raised when a request is invalid or malformed.
    """

    pass


# =====================================================
# User Exceptions
# =====================================================


class UserAlreadyExistsException(AppException):
    """
    Raised when username or email already exists.
    """


class UserNotFoundException(AppException):
    """
    Raised when user does not exist.
    """


class InvalidCredentialsException(AppException):
    """
    Raised during authentication failure.
    """


# =====================================================
# Organization Exceptions
# =====================================================


class OrganizationAlreadyExistsException(AppException):
    pass


class OrganizationNotFoundException(AppException):
    pass


class OrganizationMemberAlreadyExistsException(AppException):
    pass


class OrganizationMemberNotFoundException(AppException):
    pass


# =====================================================
# Permission Exceptions
# =====================================================


class UnauthorizedException(AppException):
    pass


class ForbiddenException(AppException):
    pass


# =====================================================
# Role Exceptions
# =====================================================


class RoleAlreadyExistsException(AppException):
    """
    Raised when a role with the same name or code already exists.
    """

    pass


class RoleNotFoundException(AppException):
    """
    Raised when the requested role does not exist.
    """

    pass

# =====================================================
# Batch Exceptions
# =====================================================


class BatchAlreadyExistsException(AppException):
    """
    Raised when a batch with the same code already exists.
    """

    pass


class BatchNotFoundException(AppException):
    """
    Raised when the requested batch does not exist.
    """

    pass


class BatchMemberAlreadyExistsException(AppException):
    """
    Raised when the organization member is already assigned
    to the batch.
    """

    pass


class BatchMemberNotFoundException(AppException):
    """
    Raised when the requested batch member does not exist.
    """

    pass

# =====================================================
# Batch Exceptions
# =====================================================


class BatchAlreadyExistsException(AppException):
    """
    Raised when a batch already exists for the same organization,
    year, and quarter.
    """
    pass


class BatchNotFoundException(AppException):
    """
    Raised when the requested batch does not exist.
    """
    pass


class BatchMemberAlreadyExistsException(AppException):
    """
    Raised when an organization member is already assigned
    to the batch.
    """
    pass


class BatchMemberNotFoundException(AppException):
    """
    Raised when the batch member mapping does not exist.
    """
    pass

# =====================================================
# OKR Exceptions
# =====================================================


class OKRAlreadyExistsException(AppException):
    """
    Raised when an OKR already exists.
    """
    pass


class OKRNotFoundException(AppException):
    """
    Raised when the requested OKR does not exist.
    """
    pass


# =====================================================
# Weekly Update Exceptions
# =====================================================


class WeeklyUpdateAlreadyExistsException(AppException):
    """
    Raised when a weekly update for the specified OKR and week already exists.
    """
    pass


class WeeklyUpdateNotFoundException(AppException):
    """
    Raised when the requested weekly update does not exist.
    """
    pass


# =====================================================
# Tracker Entry Exceptions
# =====================================================


class TrackerEntryAlreadyExistsException(AppException):
    """
    Raised when a tracker entry for the specified OKR and week start date already exists.
    """
    pass


class TrackerEntryNotFoundException(AppException):
    """
    Raised when the requested tracker entry does not exist.
    """
    pass

# =====================================================

# FOGS & Hurdles Exceptions

# =====================================================

class FogsHurdleNotFoundException(AppException):
    """
    Raised when the requested FOGS & Hurdle record does not exist.
    """
    pass

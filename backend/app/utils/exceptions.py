class AppException(Exception):
    """Base class for all application-raised HTTP errors.

    Services raise these directly; the handler registered in
    middleware/error_handler.py turns them into a consistent JSON shape.
    """

    status_code = 400
    message = "An error occurred"

    def __init__(self, message: str | None = None, status_code: int | None = None):
        self.message = message or self.message
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class InvalidCredentialsException(AppException):
    status_code = 401
    message = "Invalid email or password"


class UserAlreadyExistsException(AppException):
    status_code = 409
    message = "An account with this email already exists"


class UserNotFoundException(AppException):
    status_code = 404
    message = "User not found"


class TokenExpiredException(AppException):
    status_code = 401
    message = "Token has expired"


class InvalidTokenException(AppException):
    status_code = 401
    message = "Invalid authentication token"


class InvalidResetTokenException(AppException):
    status_code = 400
    message = "Invalid or expired reset token"


class ForbiddenException(AppException):
    status_code = 403
    message = "You do not have permission to perform this action"

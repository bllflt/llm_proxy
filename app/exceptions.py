"""Custom exception classes and error handlers."""

from fastapi import HTTPException, status


class APIException(HTTPException):
    """Base API exception."""

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedException(APIException):
    """Raised when a request is not authenticated."""

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(APIException):
    """Raised when a request is forbidden."""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(APIException):
    """Raised when a resource is not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class BadRequestException(APIException):
    """Raised when a request is malformed."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)

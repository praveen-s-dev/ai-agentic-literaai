"""
Custom Exceptions for Academic Clients

Defines custom exception classes for better error handling and debugging.
"""

from typing import Optional


class AcademicClientError(Exception):
    """Base exception for academic client errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class RateLimitError(AcademicClientError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class AuthenticationError(AcademicClientError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class NotFoundError(AcademicClientError):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class ValidationError(AcademicClientError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=400, **kwargs)


class ServerError(AcademicClientError):
    """Raised when server returns 5xx error."""
    
    def __init__(self, message: str, status_code: int = 500, **kwargs):
        super().__init__(message, status_code=status_code, **kwargs)


class NetworkError(AcademicClientError):
    """Raised when network request fails."""
    
    def __init__(self, message: str, original_exception: Optional[Exception] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.original_exception = original_exception


class TimeoutError(AcademicClientError):
    """Raised when request times out."""
    
    def __init__(self, message: str = "Request timed out", **kwargs):
        super().__init__(message, **kwargs)


class CacheError(AcademicClientError):
    """Raised when cache operations fail."""
    
    def __init__(self, message: str, operation: str = "unknown", **kwargs):
        super().__init__(message, **kwargs)
        self.operation = operation


def map_http_error(status_code: int, message: str) -> AcademicClientError:
    """Map HTTP status code to appropriate exception."""
    if status_code == 400:
        return ValidationError(message)
    elif status_code == 401:
        return AuthenticationError(message)
    elif status_code == 403:
        return AuthenticationError("Access forbidden")
    elif status_code == 404:
        return NotFoundError(message)
    elif status_code == 429:
        return RateLimitError(message)
    elif 500 <= status_code < 600:
        return ServerError(message, status_code=status_code)
    else:
        return AcademicClientError(message, status_code=status_code)
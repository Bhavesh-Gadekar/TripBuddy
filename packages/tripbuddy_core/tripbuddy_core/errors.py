from typing import Any, Optional


class TripBuddyError(Exception):
    """Base error for all TripBuddy domain exceptions."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class DatesUnavailableError(TripBuddyError):
    def __init__(self, message: str = "Requested dates are already booked or unavailable"):
        super().__init__(message, code="DATES_UNAVAILABLE")


class InvalidGuestsError(TripBuddyError):
    def __init__(self, message: str = "Guest count is outside allowed listing limits"):
        super().__init__(message, code="INVALID_GUESTS")


class InvalidDatesError(TripBuddyError):
    def __init__(self, message: str = "Check-out must be after check-in, and dates cannot be in the past"):
        super().__init__(message, code="INVALID_DATES")


class ResourceNotFoundError(TripBuddyError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND")


class UnauthorizedError(TripBuddyError):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, code="UNAUTHORIZED")


class ValidationError(TripBuddyError):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code="VALIDATION_ERROR")


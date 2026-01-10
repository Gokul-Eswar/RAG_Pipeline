"""Custom exception classes for the application."""

class AppError(Exception):
    """Base exception for application errors."""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ServiceUnavailableError(AppError):
    """Raised when an external service is unavailable."""
    def __init__(self, service_name: str, details: dict = None):
        super().__init__(
            message=f"{service_name} service is currently unavailable",
            status_code=503,
            details=details
        )

class ResourceNotFoundError(AppError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str, details: dict = None):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            status_code=404,
            details=details
        )

class AuthenticationError(AppError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(
            message=message,
            status_code=401,
            details=details
        )

class CircuitOpenError(ServiceUnavailableError):
    """Raised when a circuit breaker is open."""
    def __init__(self, service_name: str, details: dict = None):
        super().__init__(
            service_name=f"{service_name} (Circuit Open)",
            details=details
        )

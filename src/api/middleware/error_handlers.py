"""API middleware and error handlers."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from circuitbreaker import CircuitBreakerError
from src.utils.exceptions import AppError

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with custom response format."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


async def app_exception_handler(request: Request, exc: AppError):
    """Handle application-specific exceptions."""
    logger.error(f"AppError: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.__class__.__name__,
            "details": exc.details
        },
    )


async def circuit_breaker_handler(request: Request, exc: CircuitBreakerError):
    """Handle open circuit breaker exceptions."""
    logger.error(f"CircuitBreakerError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Service temporarily unavailable due to high failure rate",
            "error_code": "CircuitOpenError"
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error occurred")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "InternalError"
        },
    )

"""Resilience utilities for retry logic and circuit breakers."""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from circuitbreaker import circuit
import logging
from src.utils.config import Config

logger = logging.getLogger(__name__)

# Standard retry configuration
def get_retry_decorator(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    exceptions: tuple = (Exception,)
):
    """Create a standard retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on
        
    Returns:
        Tenacity retry decorator
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying {retry_state.fn.__name__} after error: {retry_state.outcome.exception()}"
        )
    )

# Standard circuit breaker configuration
def get_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    name: str = None
):
    """Create a standard circuit breaker.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        name: Name of the circuit breaker
        
    Returns:
        Circuit breaker decorator
    """
    return circuit(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        name=name
    )

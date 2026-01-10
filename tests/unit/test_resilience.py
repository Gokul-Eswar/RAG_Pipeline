"""Unit tests for resilience patterns."""

import pytest
from unittest.mock import MagicMock
from tenacity import RetryError
from circuitbreaker import CircuitBreakerError
from src.utils.resilience import get_retry_decorator, get_circuit_breaker

class TestRetryLogic:
    """Tests for retry decorator."""

    def test_retry_on_exception(self):
        """Test that the function retries on specified exceptions."""
        mock_func = MagicMock(side_effect=[ValueError("Fail"), "Success"])
        
        @get_retry_decorator(max_attempts=3, min_wait=0.1, max_wait=0.2, exceptions=(ValueError,))
        def decorated_func():
            return mock_func()
        
        result = decorated_func()
        assert result == "Success"
        assert mock_func.call_count == 2

    def test_retry_exhaustion(self):
        """Test that RetryError is raised after max attempts."""
        mock_func = MagicMock(side_effect=ValueError("Fail"))
        
        @get_retry_decorator(max_attempts=2, min_wait=0.1, max_wait=0.2, exceptions=(ValueError,))
        def decorated_func():
            return mock_func()
        
        with pytest.raises(RetryError):
            decorated_func()
        assert mock_func.call_count == 2


class TestCircuitBreaker:
    """Tests for circuit breaker."""

    def test_circuit_breaker_opens(self):
        """Test that circuit opens after failure threshold."""
        # Use a unique name to avoid sharing state with other tests
        cb = get_circuit_breaker(failure_threshold=2, recovery_timeout=60, name="test_cb")
        mock_func = MagicMock(side_effect=Exception("Fail"))
        
        @cb
        def decorated_func():
            return mock_func()
        
        # 1st failure
        with pytest.raises(Exception):
            decorated_func()
            
        # 2nd failure (threshold reached)
        with pytest.raises(Exception):
            decorated_func()
            
        # Circuit should now be open
        with pytest.raises(CircuitBreakerError):
            decorated_func()

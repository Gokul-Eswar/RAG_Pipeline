"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.security import get_current_active_user, User


@pytest.fixture
def api_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_client():
    """Authenticated FastAPI test client."""
    # Override the dependency for testing
    def override_get_current_active_user():
        return User(username="testuser", disabled=False)
    
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    client = TestClient(app)
    yield client
    # Clean up the override after the test
    app.dependency_overrides.clear()


@pytest.fixture
def sample_event():
    """Sample event for testing."""
    return {
        "id": "test_event_001",
        "text": "Test event content",
        "metadata": {"source": "test"}
    }


@pytest.fixture
def sample_vector():
    """Sample vector for testing."""
    return {
        "id": 1,
        "vector": [0.1] * 384,
        "payload": {"text": "Test document"}
    }


@pytest.fixture
def sample_node():
    """Sample graph node for testing."""
    return {
        "label": "TestEntity",
        "properties": {
            "name": "Test",
            "id": "test_001"
        }
    }

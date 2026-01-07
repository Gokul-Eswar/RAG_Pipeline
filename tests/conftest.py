"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def api_client():
    """FastAPI test client."""
    return TestClient(app)


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

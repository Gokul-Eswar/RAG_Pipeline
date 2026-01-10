"""Integration tests for observability features."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

class TestObservability:
    """Tests for observability endpoints."""

    def test_metrics_endpoint(self, client):
        """Test that /metrics returns Prometheus formatted data."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
        assert "http_request_duration_seconds" in response.text

    def test_liveness_probe(self, client):
        """Test liveness probe returns 200."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_readiness_probe(self, client):
        """Test readiness probe structure."""
        response = client.get("/health/ready")
        # Can be 200 or 503 depending on environment, but must have structure
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "neo4j" in data["checks"]
        assert "qdrant" in data["checks"]

    def test_correlation_id(self, client):
        """Test that correlation ID is returned in headers."""
        response = client.get("/health/live")
        assert "X-Correlation-ID" in response.headers
        
    def test_custom_correlation_id(self, client):
        """Test that custom correlation ID is respected."""
        custom_id = "test-correlation-id"
        response = client.get(
            "/health/live",
            headers={"X-Correlation-ID": custom_id}
        )
        assert response.headers["X-Correlation-ID"] == custom_id

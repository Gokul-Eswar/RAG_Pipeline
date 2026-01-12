"""Integration tests for hybrid retrieval API."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

class TestHybridRetrieval:
    """Test suite for hybrid retrieval logic."""

    def test_hybrid_health_endpoint(self, client):
        """Verify the hybrid health check endpoint."""
        response = client.get("/health/hybrid")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "neo4j" in data["components"]
        assert "qdrant" in data["components"]

    def test_hybrid_search_endpoint(self, client):
        """Verify the hybrid search endpoint."""
        payload = {
            "query_text": "Who is the CEO of Tesla?",
            "limit": 5
        }
        response = client.post("/memory/search/hybrid", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "results" in data
        assert "semantic" in data["results"]
        assert "structural" in data["results"]
        assert "meta" in data
        assert data["meta"]["vector_engine"] == "qdrant"
        assert data["meta"]["graph_engine"] == "neo4j"

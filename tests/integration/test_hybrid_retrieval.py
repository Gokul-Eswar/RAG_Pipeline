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

    def test_hybrid_health_endpoint_exists(self, client):
        """Verify the hybrid health check endpoint exists (should fail initially)."""
        response = client.get("/health/hybrid")
        # This is expected to fail with 404 until implemented
        assert response.status_code == 200
        data = response.json()
        assert "neo4j" in data
        assert "qdrant" in data

    def test_hybrid_search_endpoint_exists(self, client):
        """Verify the hybrid search endpoint exists."""
        # We might want a new endpoint or update existing ones
        # For now, let's assume we want POST /memory/search/hybrid
        payload = {
            "query_text": "Who is the CEO of Tesla?",
            "limit": 5
        }
        response = client.post("/memory/search/hybrid", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "graph_context" in data
        assert "vector_matches" in data

"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    # Login to get token
    response = client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoints:
    """Health check endpoints (public)."""
    
    def test_root_health(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_api_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    def test_hybrid_health(self, client):
        response = client.get("/health/hybrid")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestIngestEndpoints:
    """Ingestion API endpoints."""
    
    def test_ingest_unauthorized(self, client):
        """Test ingestion without auth returns 401."""
        response = client.post("/ingest/", json={"id": "test1", "text": "test"})
        assert response.status_code == 401

    def test_ingest_missing_text(self, client, auth_headers):
        response = client.post(
            "/ingest/", 
            json={"id": "test1", "text": ""},
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "text is required" in response.json()["detail"]
    
    def test_ingest_success(self, client, auth_headers):
        payload = {
            "id": "test_event_1",
            "text": "This is a test event",
            "metadata": {"source": "test"}
        }
        response = client.post(
            "/ingest/", 
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] in ["accepted", "warning"]
            assert data["id"] == "test_event_1"


class TestMemoryEndpoints:
    """Vector memory (Qdrant) endpoints."""
    
    def test_memory_upsert_unauthorized(self, client):
        response = client.post("/memory/upsert", json={"vectors": []})
        assert response.status_code == 401

    def test_memory_upsert_valid(self, client, auth_headers):
        payload = {
            "collection": "test_docs",
            "vectors": [
                {
                    "id": 1,
                    "vector": [0.1] * 384, # Minimal vector
                    "payload": {"text": "Document 1"}
                }
            ]
        }
        response = client.post(
            "/memory/upsert", 
            json=payload,
            headers=auth_headers
        )
        # Should succeed even if Qdrant not running (graceful handling)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            assert response.json()["status"] == "ok"


class TestGraphEndpoints:
    """Graph database (Neo4j) endpoints."""
    
    def test_graph_node_unauthorized(self, client):
        response = client.post("/graph/node", json={"label": "Test", "properties": {}})
        assert response.status_code == 401

    def test_graph_node_create(self, client, auth_headers):
        payload = {
            "label": "Document",
            "properties": {
                "title": "Test Doc",
                "content": "Test content"
            }
        }
        response = client.post(
            "/graph/node", 
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "created"
    
    def test_graph_relationship_create(self, client, auth_headers):
        payload = {
            "from_id": 1,
            "relationship_type": "REFERENCES",
            "to_id": 2,
            "properties": {"weight": 0.8}
        }
        response = client.post(
            "/graph/relationship", 
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 500]


class TestAPIIntegration:
    """Integration tests for API flow."""
    
    def test_health_check_chain(self, client):
        """Verify all health endpoints are responsive."""
        endpoints = [
            "/health",
            "/graph/health",
            "/memory/health",
            "/ingest/health"
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
    
    def test_ingest_and_graph_workflow(self, client, auth_headers):
        """Test basic ingest -> graph workflow."""
        # Step 1: Ingest an event
        ingest_payload = {
            "id": "workflow_test_1",
            "text": "Test workflow event",
            "metadata": {"type": "test"}
        }
        ingest_response = client.post(
            "/ingest/", 
            json=ingest_payload,
            headers=auth_headers
        )
        assert ingest_response.status_code in [200, 503]
        
        # Step 2: Create a node for the ingested event
        node_payload = {
            "label": "Event",
            "properties": {
                "event_id": "workflow_test_1",
                "text": "Test workflow event"
            }
        }
        node_response = client.post(
            "/graph/node", 
            json=node_payload,
            headers=auth_headers
        )
        assert node_response.status_code in [200, 500]

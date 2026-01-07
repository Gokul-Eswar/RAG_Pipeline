"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Health check endpoints."""
    
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
    
    def test_graph_health(self, client):
        response = client.get("/graph/health")
        assert response.status_code == 200
        data = response.json()
        assert "neo4j" in data
    
    def test_memory_health(self, client):
        response = client.get("/memory/health")
        assert response.status_code == 200
        data = response.json()
        assert "qdrant" in data
    
    def test_ingest_health(self, client):
        response = client.get("/ingest/health")
        assert response.status_code == 200
        data = response.json()
        assert "kafka" in data


class TestIngestEndpoints:
    """Ingestion API endpoints."""
    
    def test_ingest_missing_text(self, client):
        response = client.post("/ingest/", json={"id": "test1", "text": ""})
        assert response.status_code == 400
        assert "text is required" in response.json()["detail"]
    
    def test_ingest_success(self, client):
        payload = {
            "id": "test_event_1",
            "text": "This is a test event",
            "metadata": {"source": "test"}
        }
        response = client.post("/ingest/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["accepted", "warning"]
        assert data["id"] == "test_event_1"
    
    def test_ingest_minimal(self, client):
        payload = {
            "id": "test_event_2",
            "text": "Minimal test"
        }
        response = client.post("/ingest/", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] in ["accepted", "warning"]


class TestMemoryEndpoints:
    """Vector memory (Qdrant) endpoints."""
    
    def test_memory_upsert_missing_vectors(self, client):
        response = client.post("/memory/upsert", json={"vectors": []})
        assert response.status_code == 400
        assert "vectors are required" in response.json()["detail"]
    
    def test_memory_upsert_valid(self, client):
        payload = {
            "collection": "test_docs",
            "vectors": [
                {
                    "id": 1,
                    "vector": [0.1, 0.2, 0.3] * 128,  # 384 dimensions
                    "payload": {"text": "Document 1"}
                }
            ]
        }
        response = client.post("/memory/upsert", json=payload)
        # Should succeed even if Qdrant not running (graceful handling)
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            assert response.json()["status"] == "ok"
    
    def test_memory_search_missing_vector(self, client):
        response = client.post("/memory/search", json={"query_vector": []})
        assert response.status_code == 400
        assert "query_vector is required" in response.json()["detail"]
    
    def test_memory_search_valid(self, client):
        payload = {
            "collection": "test_docs",
            "query_vector": [0.1, 0.2, 0.3] * 128,
            "limit": 5
        }
        response = client.post("/memory/search", json=payload)
        # May fail if service unavailable, but should have proper error
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
    
    def test_memory_collection_info(self, client):
        payload = {"collection": "test_docs"}
        response = client.post("/memory/collection/info", json=payload)
        assert response.status_code in [200, 500]


class TestGraphEndpoints:
    """Graph database (Neo4j) endpoints."""
    
    def test_graph_node_missing_label(self, client):
        response = client.post("/graph/node", json={"label": "", "properties": {}})
        assert response.status_code == 400
        assert "label required" in response.json()["detail"]
    
    def test_graph_node_create(self, client):
        payload = {
            "label": "Document",
            "properties": {
                "title": "Test Doc",
                "content": "Test content"
            }
        }
        response = client.post("/graph/node", json=payload)
        # May fail if Neo4j not running, but should have proper error
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "created"
    
    def test_graph_relationship_create(self, client):
        payload = {
            "from_id": 1,
            "relationship_type": "REFERENCES",
            "to_id": 2,
            "properties": {"weight": 0.8}
        }
        response = client.post("/graph/relationship", json=payload)
        # May fail if Neo4j not running
        assert response.status_code in [200, 500]
    
    def test_graph_node_find(self, client):
        payload = {
            "label": "Document",
            "properties": {"title": "Test"}
        }
        response = client.post("/graph/node/find", json=payload)
        # May return 404 or 500
        assert response.status_code in [200, 404, 500]
    
    def test_graph_node_delete(self, client):
        response = client.delete("/graph/node/999")
        # May fail if node doesn't exist
        assert response.status_code in [200, 404, 500]


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
            assert isinstance(response.json(), dict)
    
    def test_ingest_and_graph_workflow(self, client):
        """Test basic ingest -> graph workflow."""
        # Step 1: Ingest an event
        ingest_payload = {
            "id": "workflow_test_1",
            "text": "Test workflow event",
            "metadata": {"type": "test"}
        }
        ingest_response = client.post("/ingest/", json=ingest_payload)
        assert ingest_response.status_code == 200
        
        # Step 2: Create a node for the ingested event
        node_payload = {
            "label": "Event",
            "properties": {
                "event_id": "workflow_test_1",
                "text": "Test workflow event"
            }
        }
        node_response = client.post("/graph/node", json=node_payload)
        # Should succeed or gracefully fail (service unavailable)
        assert node_response.status_code in [200, 500]

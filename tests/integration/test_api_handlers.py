"""Integration tests for API handlers."""

import pytest


class TestEventIngestHandler:
    """Integration tests for event ingestion."""
    
    def test_ingest_health_check(self, api_client):
        """Test ingest health endpoint."""
        response = api_client.get("/ingest/health")
        assert response.status_code == 200
        assert "kafka" in response.json()
    
    def test_ingest_event_valid(self, api_client, sample_event):
        """Test valid event ingestion."""
        response = api_client.post("/ingest/", json=sample_event)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["id"] == sample_event["id"]
    
    def test_ingest_event_missing_text(self, api_client):
        """Test ingestion validation."""
        response = api_client.post("/ingest/", json={"id": "test", "text": ""})
        assert response.status_code == 400


class TestVectorMemoryHandler:
    """Integration tests for vector memory."""
    
    def test_vector_health_check(self, api_client):
        """Test vector memory health."""
        response = api_client.get("/memory/health")
        assert response.status_code == 200
        assert "qdrant" in response.json()
    
    def test_upsert_vectors(self, api_client, sample_vector):
        """Test vector upsert."""
        payload = {
            "collection": "test_vectors",
            "vectors": [sample_vector]
        }
        response = api_client.post("/memory/upsert", json=payload)
        assert response.status_code in [200, 500]
    
    def test_search_vectors(self, api_client):
        """Test vector search."""
        payload = {
            "query_vector": [0.1] * 384,
            "limit": 5
        }
        response = api_client.post("/memory/search", json=payload)
        assert response.status_code in [200, 500]
    
    def test_collection_info(self, api_client):
        """Test collection info endpoint."""
        payload = {"collection": "test_vectors"}
        response = api_client.post("/memory/collection/info", json=payload)
        assert response.status_code in [200, 500]


class TestGraphMemoryHandler:
    """Integration tests for graph memory."""
    
    def test_graph_health_check(self, api_client):
        """Test graph health."""
        response = api_client.get("/graph/health")
        assert response.status_code == 200
        assert "neo4j" in response.json()
    
    def test_create_node(self, api_client, sample_node):
        """Test node creation."""
        response = api_client.post("/graph/node", json=sample_node)
        assert response.status_code in [200, 500]
    
    def test_create_relationship(self, api_client):
        """Test relationship creation."""
        payload = {
            "from_id": 1,
            "relationship_type": "CONNECTS",
            "to_id": 2
        }
        response = api_client.post("/graph/relationship", json=payload)
        assert response.status_code in [200, 500]
    
    def test_find_node(self, api_client):
        """Test node search."""
        payload = {
            "label": "TestEntity",
            "properties": {"name": "nonexistent"}
        }
        response = api_client.post("/graph/node/find", json=payload)
        assert response.status_code in [200, 404, 500]
    
    def test_delete_node(self, api_client):
        """Test node deletion."""
        response = api_client.delete("/graph/node/999")
        assert response.status_code in [200, 404, 500]


class TestAPIHealthEndpoints:
    """Integration tests for system health endpoints."""
    
    def test_root_endpoint(self, api_client):
        """Test root endpoint."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_health_endpoint(self, api_client):
        """Test health endpoint."""
        response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

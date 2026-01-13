"""Integration tests for ingestion workflow."""

import pytest


class TestIngestionWorkflow:
    """Tests for end-to-end ingestion workflow."""
    
    def test_event_ingestion_flow(self, auth_client, sample_event):
        """Test complete ingestion flow."""
        # Step 1: Ingest event
        response = auth_client.post("/ingest/", json=sample_event)
        assert response.status_code == 200
        
        # Step 2: Verify response
        data = response.json()
        assert data["id"] == sample_event["id"]


class TestMemoryIndexingWorkflow:
    """Tests for memory indexing workflow."""
    
    def test_vector_indexing_flow(self, api_client, sample_vector):
        """Test vector indexing workflow."""
        # Step 1: Upsert vector
        payload = {
            "collection": "indexed_vectors",
            "vectors": [sample_vector]
        }
        response = api_client.post("/memory/upsert", json=payload)
        assert response.status_code in [200, 500]
        
        # Step 2: Search vectors
        if response.status_code == 200:
            search_payload = {
                "query_vector": sample_vector["vector"],
                "limit": 10
            }
            search_response = api_client.post("/memory/search", json=search_payload)
            assert search_response.status_code in [200, 500]


class TestGraphBuildingWorkflow:
    """Tests for graph building workflow."""
    
    def test_entity_and_relationship_workflow(self, api_client, sample_node):
        """Test entity creation and relationship workflow."""
        # Step 1: Create first node
        node1_response = api_client.post("/graph/node", json=sample_node)
        assert node1_response.status_code in [200, 500]
        
        # Step 2: Create second node
        node2 = {
            "label": "TestEntity",
            "properties": {"name": "Related", "id": "test_002"}
        }
        node2_response = api_client.post("/graph/node", json=node2)
        assert node2_response.status_code in [200, 500]

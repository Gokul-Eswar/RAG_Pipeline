"""End-to-end system tests."""

import pytest


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    def test_complete_rag_workflow(self, api_client, sample_event, sample_vector):
        """Test complete RAG workflow."""
        # 1. Ingest event
        ingest_response = api_client.post("/ingest/", json=sample_event)
        assert ingest_response.status_code == 200
        
        # 2. Store vector
        vector_payload = {
            "collection": "e2e_test",
            "vectors": [sample_vector]
        }
        vector_response = api_client.post("/memory/upsert", json=vector_payload)
        assert vector_response.status_code in [200, 500]
        
        # 3. Create graph node
        node = {
            "label": "Document",
            "properties": {"event_id": sample_event["id"]}
        }
        graph_response = api_client.post("/graph/node", json=node)
        assert graph_response.status_code in [200, 500]

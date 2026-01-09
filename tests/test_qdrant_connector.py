"""Unit tests for Qdrant connector."""

import pytest
from src.infrastructure.database.qdrant import QdrantVectorRepository


class TestQdrantVectorRepository:
    """Tests for Qdrant vector store."""

    @pytest.fixture
    def store(self):
        """Create a vector store instance."""
        return QdrantVectorRepository("test_collection")

    def test_store_initialization(self, store):
        """Test store can be initialized."""
        assert store is not None
        assert store.collection_name == "test_collection"

    def test_store_default_collection(self):
        """Test store uses default collection name."""
        store = QdrantVectorRepository()
        assert store.collection_name is not None
        assert isinstance(store.collection_name, str)
    def test_create_collection_structure(self, store):
        """Test create_collection returns boolean."""
        if store.client is not None:
            result = store.create_collection(vector_size=384)
            assert isinstance(result, bool)
    
    def test_get_collection_info_structure(self, store):
        """Test collection info returns expected structure."""
        result = store.get_collection_info()
        assert isinstance(result, dict)
        if "error" not in result:
            assert "name" in result
            assert "points_count" in result


class TestVectorOperations:
    """Tests for vector operations."""
    
    @pytest.fixture
    def store(self):
        return QdrantVectorRepository("test_collection")
    
    def test_upsert_structure(self, store):
        """Test upsert returns expected structure."""
        vectors = [
            {
                "id": 1,
                "vector": [0.1] * 384,
                "payload": {"text": "Document 1"}
            }
        ]
        result = store.upsert(vectors)
        assert isinstance(result, dict)
        if "error" not in result:
            assert "status" in result
            assert "count" in result
            assert result["count"] == 1
    
    def test_upsert_multiple_vectors(self, store):
        """Test upserting multiple vectors."""
        vectors = [
            {
                "id": i,
                "vector": [0.1 * (i % 10)] * 384,
                "payload": {"text": f"Document {i}"}
            }
            for i in range(5)
        ]
        result = store.upsert(vectors)
        assert isinstance(result, dict)
    
    def test_search_structure(self, store):
        """Test search returns list."""
        query_vector = [0.1] * 384
        result = store.search(query_vector, limit=10)
        assert isinstance(result, list)
    
    def test_search_with_limit(self, store):
        """Test search respects limit parameter."""
        query_vector = [0.1] * 384
        result = store.search(query_vector, limit=5)
        assert isinstance(result, list)
        assert len(result) <= 5
    
    def test_delete_structure(self, store):
        """Test delete returns boolean."""
        result = store.delete([1, 2, 3])
        assert isinstance(result, bool)


class TestVectorStoreEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def store(self):
        return QdrantVectorRepository("edge_case_collection")
    
    def test_empty_upsert(self, store):
        """Test upserting empty list."""
        result = store.upsert([])
        assert isinstance(result, dict)
    
    def test_search_empty_vector(self, store):
        """Test searching with empty vector."""
        result = store.search([], limit=10)
        assert isinstance(result, list)
    
    def test_delete_nonexistent_ids(self, store):
        """Test deleting non-existent IDs."""
        result = store.delete([9999, 10000])
        assert isinstance(result, bool)
    
    def test_vector_dimension_consistency(self, store):
        """Test vectors with consistent dimensions."""
        vectors = [
            {
                "id": i,
                "vector": [0.5] * 384,
                "payload": {"index": i}
            }
            for i in range(3)
        ]
        result = store.upsert(vectors)
        assert isinstance(result, dict)


class TestQdrantClientAvailability:
    """Tests for graceful handling when Qdrant is unavailable."""
    
    def test_store_with_unavailable_client(self):
        """Test store handles unavailable client gracefully."""
        store = QdrantVectorRepository("test")
        # If client is None, operations should return graceful responses
        if store.client is None:
            result = store.upsert([{"id": 1, "vector": [0.1]}])
            assert "error" in result

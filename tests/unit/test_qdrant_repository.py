"""Unit tests for Qdrant vector repository."""

import pytest
from src.infrastructure.database.qdrant import QdrantVectorRepository


class TestQdrantVectorRepository:
    """Tests for Qdrant vector repository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository instance."""
        return QdrantVectorRepository("test_collection")
    
    def test_repository_initialization(self, repository):
        """Test repository can be initialized."""
        assert repository is not None
        assert repository.collection_name == "test_collection"
    
    def test_collection_info_structure(self, repository):
        """Test collection info returns expected structure."""
        result = repository.get_collection_info()
        assert isinstance(result, dict)
        if "error" not in result:
            assert "name" in result
            assert "points_count" in result


class TestVectorOperations:
    """Tests for vector operations."""
    
    @pytest.fixture
    def repository(self):
        return QdrantVectorRepository("test_vectors")
    
    def test_upsert_structure(self, repository):
        """Test upsert returns expected structure."""
        vectors = [{"id": 1, "vector": [0.1] * 384, "payload": {"text": "test"}}]
        result = repository.upsert(vectors)
        assert isinstance(result, dict)
        if "error" not in result:
            assert "status" in result
            assert "count" in result
    
    def test_search_structure(self, repository):
        """Test search returns list."""
        result = repository.search([0.1] * 384, limit=10)
        assert isinstance(result, list)
    
    def test_delete_returns_boolean(self, repository):
        """Test delete returns boolean."""
        result = repository.delete([1, 2])
        assert isinstance(result, bool)


class TestVectorRepositoryEdgeCases:
    """Tests for edge cases."""
    
    @pytest.fixture
    def repository(self):
        return QdrantVectorRepository("edge_cases")
    
    def test_empty_upsert(self, repository):
        """Test empty upsert."""
        result = repository.upsert([])
        assert isinstance(result, dict)
    
    def test_search_with_zero_limit(self, repository):
        """Test search with zero limit."""
        result = repository.search([0.1] * 384, limit=0)
        assert isinstance(result, list)

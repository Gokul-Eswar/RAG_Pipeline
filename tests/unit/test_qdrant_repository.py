"""Unit tests for Qdrant vector repository."""

import pytest
from unittest.mock import MagicMock, patch
from src.infrastructure.database.qdrant import QdrantVectorRepository


class TestQdrantVectorRepository:
    """Tests for Qdrant vector repository."""
    
    @pytest.fixture
    def mock_client(self):
        with patch("src.infrastructure.database.qdrant.QdrantClient") as mock_qdrant:
            mock_client = MagicMock()
            mock_qdrant.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def repository(self, mock_client):
        """Create a repository instance with mocked client."""
        return QdrantVectorRepository("test_collection")
    
    def test_repository_initialization(self, repository):
        """Test repository can be initialized."""
        assert repository is not None
        assert repository.collection_name == "test_collection"
    
    def test_collection_info_structure(self, repository, mock_client):
        """Test collection info returns expected structure."""
        mock_info = MagicMock()
        mock_info.points_count = 10
        mock_info.vectors_count = 10
        mock_info.config = {}
        mock_client.get_collection.return_value = mock_info

        result = repository.get_collection_info()
        assert isinstance(result, dict)
        assert result["name"] == "test_collection"
        assert result["points_count"] == 10


class TestVectorOperations:
    """Tests for vector operations."""
    
    @pytest.fixture
    def mock_client(self):
        with patch("src.infrastructure.database.qdrant.QdrantClient") as mock_qdrant:
            mock_client = MagicMock()
            mock_qdrant.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def repository(self, mock_client):
        return QdrantVectorRepository("test_vectors")
    
    def test_upsert_structure(self, repository, mock_client):
        """Test upsert returns expected structure."""
        vectors = [{"id": 1, "vector": [0.1] * 384, "payload": {"text": "test"}}]
        mock_client.upsert.return_value = None
        
        result = repository.upsert(vectors)
        assert isinstance(result, dict)
        assert result["status"] == "ok"
        assert result["count"] == 1
    
    def test_search_structure(self, repository, mock_client):
        """Test search returns list."""
        mock_points = MagicMock()
        mock_point = MagicMock()
        mock_point.id = 1
        mock_point.score = 0.99
        mock_point.payload = {"text": "test"}
        mock_points.points = [mock_point]
        mock_client.query_points.return_value = mock_points

        result = repository.search([0.1] * 384, limit=10)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1
    
    def test_delete_returns_boolean(self, repository, mock_client):
        """Test delete returns boolean."""
        mock_client.delete.return_value = None
        result = repository.delete([1, 2])
        assert isinstance(result, bool)
        assert result is True


class TestVectorRepositoryEdgeCases:
    """Tests for edge cases."""
    
    @pytest.fixture
    def mock_client(self):
        with patch("src.infrastructure.database.qdrant.QdrantClient") as mock_qdrant:
            mock_client = MagicMock()
            mock_qdrant.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def repository(self, mock_client):
        return QdrantVectorRepository("edge_cases")
    
    def test_empty_upsert(self, repository, mock_client):
        """Test empty upsert."""
        result = repository.upsert([])
        assert isinstance(result, dict)
        assert result["count"] == 0
    
    def test_search_with_zero_limit(self, repository, mock_client):
        """Test search with zero limit."""
        mock_points = MagicMock()
        mock_points.points = []
        mock_client.query_points.return_value = mock_points

        result = repository.search([0.1] * 384, limit=0)
        assert isinstance(result, list)
        assert len(result) == 0

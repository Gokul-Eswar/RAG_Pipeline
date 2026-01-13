"""Unit tests for Neo4j graph repository."""

import pytest
from unittest.mock import MagicMock, patch
from src.infrastructure.database.neo4j import Neo4jGraphRepository


class TestNeo4jGraphRepository:
    """Tests for Neo4j graph repository."""
    
    @pytest.fixture
    def mock_driver(self):
        with patch("src.infrastructure.database.neo4j.GraphDatabase") as mock_db:
            mock_driver = MagicMock()
            mock_db.driver.return_value = mock_driver
            yield mock_driver

    @pytest.fixture
    def repository(self, mock_driver):
        """Create a repository instance with mocked driver."""
        repo = Neo4jGraphRepository()
        return repo
    
    def test_repository_initialization(self, repository):
        """Test repository can be initialized."""
        assert repository is not None
        repository.close()
    
    def test_create_node_structure(self, repository, mock_driver):
        """Test create_node returns expected structure."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_record = {"node_id": 1, "props": {"name": "test"}}
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result

        result = repository.create_node("TestNode", {"name": "test"})
        assert isinstance(result, dict)
        assert result["node_id"] == 1
        assert result["properties"]["name"] == "test"
    
    def test_find_node_structure(self, repository, mock_driver):
        """Test find_node returns expected structure."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_record = {"node_id": 1, "props": {"name": "test"}}
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result

        result = repository.find_node("TestNode", {"name": "test"})
        assert isinstance(result, dict)
        assert result["node_id"] == 1
    
    def test_delete_node_returns_boolean(self, repository, mock_driver):
        """Test delete_node returns boolean."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_result.summary.counters.nodes_deleted = 1
        mock_session.run.return_value = mock_result

        result = repository.delete_node(999)
        assert isinstance(result, bool)
        assert result is True


class TestNeo4jNodeOperations:
    """Tests for node operations."""
    
    @pytest.fixture
    def mock_driver(self):
        with patch("src.infrastructure.database.neo4j.GraphDatabase") as mock_db:
            mock_driver = MagicMock()
            mock_db.driver.return_value = mock_driver
            yield mock_driver

    @pytest.fixture
    def repository(self, mock_driver):
        return Neo4jGraphRepository()
    
    def test_create_multiple_node_types(self, repository, mock_driver):
        """Test creating different node types."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_result.single.return_value = {"node_id": 1, "props": {"id": "test"}}
        mock_session.run.return_value = mock_result

        labels = ["Document", "Entity", "Relation"]
        for label in labels:
            result = repository.create_node(label, {"id": "test"})
            assert isinstance(result, dict)
            assert "node_id" in result


class TestNeo4jRelationships:
    """Tests for relationship operations."""
    
    @pytest.fixture
    def mock_driver(self):
        with patch("src.infrastructure.database.neo4j.GraphDatabase") as mock_db:
            mock_driver = MagicMock()
            mock_db.driver.return_value = mock_driver
            yield mock_driver

    @pytest.fixture
    def repository(self, mock_driver):
        return Neo4jGraphRepository()
    
    def test_create_relationship_structure(self, repository, mock_driver):
        """Test relationship creation structure."""
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        
        mock_result = MagicMock()
        mock_result.single.return_value = {"rel_id": 100}
        mock_session.run.return_value = mock_result

        result = repository.create_relationship(1, "CONNECTS_TO", 2)
        assert isinstance(result, dict)
        assert result["relationship_id"] == 100

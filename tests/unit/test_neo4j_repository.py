"""Unit tests for Neo4j graph repository."""

import pytest
from src.infrastructure.database.neo4j import Neo4jGraphRepository


class TestNeo4jGraphRepository:
    """Tests for Neo4j graph repository."""
    
    @pytest.fixture
    def repository(self):
        """Create a repository instance."""
        return Neo4jGraphRepository()
    
    def test_repository_initialization(self, repository):
        """Test repository can be initialized."""
        assert repository is not None
        repository.close()
    
    def test_create_node_structure(self, repository):
        """Test create_node returns expected structure."""
        result = repository.create_node("TestNode", {"name": "test"})
        assert isinstance(result, dict)
        if "error" not in result:
            assert "node_id" in result
            assert "properties" in result
    
    def test_find_node_structure(self, repository):
        """Test find_node returns expected structure."""
        result = repository.find_node("TestNode", {"name": "nonexistent"})
        assert result is None or isinstance(result, dict)
    
    def test_delete_node_returns_boolean(self, repository):
        """Test delete_node returns boolean."""
        result = repository.delete_node(999)
        assert isinstance(result, bool)


class TestNeo4jNodeOperations:
    """Tests for node operations."""
    
    @pytest.fixture
    def repository(self):
        return Neo4jGraphRepository()
    
    def test_create_multiple_node_types(self, repository):
        """Test creating different node types."""
        labels = ["Document", "Entity", "Relation"]
        for label in labels:
            result = repository.create_node(label, {"id": "test"})
            assert isinstance(result, dict)


class TestNeo4jRelationships:
    """Tests for relationship operations."""
    
    @pytest.fixture
    def repository(self):
        return Neo4jGraphRepository()
    
    def test_create_relationship_structure(self, repository):
        """Test relationship creation structure."""
        result = repository.create_relationship(1, "CONNECTS_TO", 2)
        assert isinstance(result, dict)

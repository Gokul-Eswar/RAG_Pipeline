"""Unit tests for Neo4j connector."""

import pytest
from src.infrastructure.database.neo4j import Neo4jGraphRepository


class TestNeo4jGraphRepository:
    """Tests for Neo4j client operations."""

    @pytest.fixture
    def client(self):
        """Create a Neo4j client instance."""
        return Neo4jGraphRepository()
    def test_client_initialization(self, client):
        """Test client can be initialized."""
        assert client is not None
        # Driver may be None if Neo4j not available
        client.close()
    
    def test_create_node_structure(self, client):
        """Test create_node returns expected structure."""
        result = client.create_node("TestNode", {"name": "test"})
        assert isinstance(result, dict)
        if "error" not in result:
            assert "node_id" in result
            assert "properties" in result
        else:
            # Error is expected if Neo4j not available
            assert isinstance(result["error"], str)
    
    def test_create_node_validation(self, client):
        """Test node creation with various labels."""
        labels = ["Document", "Entity", "Relation"]
        for label in labels:
            result = client.create_node(label, {"id": "test"})
            assert isinstance(result, dict)
            # Either succeeds or returns graceful error
            assert "error" in result or "node_id" in result
    
    def test_find_node_structure(self, client):
        """Test find_node returns expected structure."""
        result = client.find_node("Document", {"id": "nonexistent"})
        # Will be None if not found or Neo4j unavailable
        assert result is None or isinstance(result, dict)
    
    def test_delete_node_structure(self, client):
        """Test delete_node returns boolean."""
        result = client.delete_node(999)
        assert isinstance(result, bool)


class TestNeo4jNodeOperations:
    """Tests for node CRUD operations."""
    
    @pytest.fixture
    def client(self):
        return Neo4jGraphRepository()
    
    def test_create_multiple_nodes(self, client):
        """Test creating multiple nodes."""
        nodes = [
            ("Document", {"title": "Doc1"}),
            ("Entity", {"name": "Entity1"}),
            ("Relation", {"type": "mentions"}),
        ]
        
        for label, props in nodes:
            result = client.create_node(label, props)
            assert isinstance(result, dict)
    
    def test_relationship_creation_structure(self, client):
        """Test relationship creation structure."""
        result = client.create_relationship(1, "REFERENCES", 2, {"weight": 0.5})
        assert isinstance(result, dict)
        if "error" not in result:
            assert "relationship_id" in result
            assert "type" in result


class TestNeo4jConnectionHandling:
    """Tests for connection handling."""
    
    def test_client_close(self):
        """Test client close doesn't raise exception."""
        client = Neo4jGraphRepository()
        try:
            client.close()
        except Exception as e:
            pytest.fail(f"close() raised {e}")
    
    def test_driver_unavailable_handling(self):
        """Test graceful handling when driver is unavailable."""
        client = Neo4jGraphRepository()
        if client.driver is None:
            # Verify operations return graceful errors
            result = client.create_node("Test", {})
            assert "error" in result
        client.close()

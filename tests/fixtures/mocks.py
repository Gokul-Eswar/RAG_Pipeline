"""Test fixtures and mocks."""

import pytest


class MockQdrantClient:
    """Mock Qdrant client for testing."""
    
    def __init__(self):
        self.collections = {}
    
    def create_collection(self, name, config):
        """Mock collection creation."""
        self.collections[name] = config
        return True
    
    def upsert(self, collection, points):
        """Mock upsert operation."""
        return True


class MockNeo4jDriver:
    """Mock Neo4j driver for testing."""
    
    def __init__(self):
        self.nodes = {}
    
    def session(self):
        """Return a mock session."""
        return MockSession(self)
    
    def close(self):
        """Mock close."""
        pass


class MockSession:
    """Mock Neo4j session."""
    
    def __init__(self, driver):
        self.driver = driver
    
    def run(self, query, **params):
        """Mock query execution."""
        return MockResult()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


class MockResult:
    """Mock query result."""
    
    def single(self):
        """Return mock record."""
        return {"node_id": 1, "props": {}}


@pytest.fixture
def mock_qdrant():
    """Provide mock Qdrant client."""
    return MockQdrantClient()


@pytest.fixture
def mock_neo4j():
    """Provide mock Neo4j driver."""
    return MockNeo4jDriver()

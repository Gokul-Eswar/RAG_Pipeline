"""Unit tests for Database Resilience (Transactions, Batching, Rollbacks)."""

import pytest
from unittest.mock import MagicMock, patch, call
from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository

class TestNeo4jResilience:
    @pytest.fixture
    def mock_driver(self):
        with patch('src.infrastructure.database.neo4j.GraphDatabase.driver') as mock:
            driver_instance = MagicMock()
            mock.return_value = driver_instance
            yield driver_instance

    @pytest.fixture
    def repo(self, mock_driver):
        return Neo4jGraphRepository()

    def test_execute_transaction_commit(self, repo, mock_driver):
        """Test that successful transaction commits."""
        session_mock = MagicMock()
        tx_mock = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = session_mock
        session_mock.begin_transaction.return_value.__enter__.return_value = tx_mock
        
        # Mock query result
        result_mock = MagicMock()
        record_mock = MagicMock()
        record_mock.data.return_value = {"id": 1}
        result_mock.__iter__.return_value = [record_mock]
        tx_mock.run.return_value = result_mock

        data = repo.execute_transaction("CREATE (n) RETURN n")
        
        assert data == [{"id": 1}]
        tx_mock.commit.assert_called_once()
        tx_mock.rollback.assert_not_called()

    def test_execute_transaction_rollback(self, repo, mock_driver):
        """Test that failed transaction rolls back."""
        session_mock = MagicMock()
        tx_mock = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = session_mock
        session_mock.begin_transaction.return_value.__enter__.return_value = tx_mock
        
        # Simulate error
        tx_mock.run.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            repo.execute_transaction("CREATE (n) RETURN n")
        
        tx_mock.commit.assert_not_called()
        tx_mock.rollback.assert_called_once()

    def test_batch_create_nodes_chunking(self, repo, mock_driver):
        """Test that batch creation is chunked correctly."""
        session_mock = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = session_mock
        
        # 150 items, batch size 100
        nodes = [{"name": f"Node{i}"} for i in range(150)]
        
        repo.batch_create_nodes("TestLabel", nodes, batch_size=100)
        
        # Should be called twice
        assert session_mock.run.call_count == 2
        
        # Check arguments of first call
        first_call_args = session_mock.run.call_args_list[0]
        # query is first arg, kwargs has 'batch'
        assert len(first_call_args.kwargs['batch']) == 100
        
        # Check arguments of second call
        second_call_args = session_mock.run.call_args_list[1]
        assert len(second_call_args.kwargs['batch']) == 50

class TestQdrantResilience:
    @pytest.fixture
    def mock_client(self):
        with patch('src.infrastructure.database.qdrant.QdrantClient') as mock:
            client_instance = MagicMock()
            mock.return_value = client_instance
            yield client_instance

    @pytest.fixture
    def repo(self, mock_client):
        # Prevent actual client init
        return QdrantVectorRepository()

    def test_upsert_batch_chunking(self, repo, mock_client):
        """Test that Qdrant upsert is chunked correctly."""
        # 150 items, batch size 100
        vectors = [{"id": i, "vector": [0.1]*384} for i in range(150)]
        
        repo.upsert(vectors, batch_size=100)
        
        assert mock_client.upsert.call_count == 2
        
        # Verify first batch size
        first_call = mock_client.upsert.call_args_list[0]
        assert len(first_call.kwargs['points']) == 100
        
        # Verify second batch size
        second_call = mock_client.upsert.call_args_list[1]
        assert len(second_call.kwargs['points']) == 50

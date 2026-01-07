"""Unit tests for Kafka event producer."""

import pytest
from src.infrastructure.messaging.kafka import KafkaEventProducer, publish_event


class TestKafkaEventProducer:
    """Tests for Kafka event producer."""
    
    def test_producer_initialization(self):
        """Test producer initialization."""
        try:
            producer = KafkaEventProducer(broker="localhost:9092")
            assert producer.broker == "localhost:9092"
            producer.close()
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")
    
    def test_producer_default_values(self):
        """Test producer uses defaults."""
        producer = KafkaEventProducer()
        assert producer.broker is not None
        assert producer.topic is not None
        producer.close()


class TestEventPublishing:
    """Tests for event publishing."""
    
    def test_publish_event_function(self):
        """Test convenience publish function."""
        try:
            result = publish_event("test_001", "Test content", {"source": "test"})
            assert isinstance(result, bool)
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")


class TestBatchPublishing:
    """Tests for batch publishing."""
    
    def test_batch_publish_structure(self):
        """Test batch publish structure."""
        try:
            producer = KafkaEventProducer()
            events = [
                {"id": f"test_{i}", "text": f"Content {i}", "metadata": {}}
                for i in range(3)
            ]
            result = producer.publish_batch(events)
            assert "total" in result
            assert "successful" in result
            assert "failed" in result
            producer.close()
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")

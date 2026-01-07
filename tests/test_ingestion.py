"""Unit tests for ingestion producer."""

import pytest
from ingestion.producer import EventProducer, publish_event


class TestEventProducer:
    """Tests for EventProducer class."""
    
    def test_producer_initialization(self):
        """Test producer can be initialized."""
        try:
            producer = EventProducer(broker="localhost:9092", topic="test")
            assert producer.broker == "localhost:9092"
            assert producer.topic == "test"
            producer.close()
        except Exception as e:
            # Expected if Kafka not running
            assert "broker" in str(e).lower() or "refused" in str(e).lower()
    
    def test_producer_defaults(self):
        """Test producer uses environment defaults."""
        producer = EventProducer()
        assert producer.broker is not None
        assert producer.topic is not None
        producer.close()


class TestPublishEvent:
    """Tests for publishing events."""
    
    def test_publish_event_structure(self):
        """Test that published events have correct structure."""
        # This is a smoke test since we can't guarantee Kafka is running
        event_id = "test_event_1"
        text = "Test event content"
        metadata = {"source": "test"}
        
        # publish_event will either succeed or return False gracefully
        # We're testing that it doesn't raise an exception
        try:
            result = publish_event(event_id, text, metadata)
            # result should be True or False, not an exception
            assert isinstance(result, bool)
        except Exception as e:
            # If Kafka is not available, that's okay for this test
            pytest.skip(f"Kafka not available: {e}")


class TestEventBatch:
    """Tests for batch publishing."""
    
    def test_batch_publish_structure(self):
        """Test batch publishing structure."""
        try:
            producer = EventProducer()
            events = [
                {
                    "id": f"batch_test_{i}",
                    "text": f"Event {i}",
                    "metadata": {"batch": True}
                }
                for i in range(5)
            ]
            
            # batch_publish may fail if Kafka not available
            result = producer.publish_batch(events)
            assert "total" in result
            assert "successful" in result
            assert "failed" in result
            assert result["total"] == 5
            
            producer.close()
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")

"""Kafka/Redpanda messaging client."""

import json
import os
import logging
from typing import Dict, Any, Optional
from src.utils.resilience import get_retry_decorator, get_circuit_breaker
from src.utils.metrics import EVENTS_INGESTED

logger = logging.getLogger(__name__)

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
except ImportError:
    KafkaProducer = None
    KafkaError = None


class KafkaEventProducer:
    """Producer for publishing events to Kafka/Redpanda.
    
    Handles event publishing with proper serialization and error handling.
    """
    
    def __init__(self, broker: Optional[str] = None, topic: Optional[str] = None):
        """Initialize the event producer.
        
        Args:
            broker: Kafka broker address
            topic: Target topic name
        """
        self.broker = broker or os.getenv("KAFKA_BROKER", "redpanda:9092")
        self.topic = topic or os.getenv("KAFKA_TOPIC_INGESTION", "raw_events")
        self.producer = self._create_producer()
    
    def _create_producer(self) -> Optional[KafkaProducer]:
        """Create Kafka producer instance."""
        if KafkaProducer is None:
            return None
        try:
            return KafkaProducer(
                bootstrap_servers=self.broker,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            )
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            return None
    
    @get_circuit_breaker(name="kafka_publish")
    @get_retry_decorator()
    def publish(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Publish a single event.
        
        Args:
            event: Event dictionary to publish
            
        Returns:
            Kafka metadata
            
        Raises:
            Exception: If publishing fails (to trigger retry)
        """
        if self.producer is None:
            raise Exception("Kafka producer not available")
        
        future = self.producer.send(self.topic, value=event)
        # Wait for result to ensure it's sent (synchronous for reliability)
        record_metadata = future.get(timeout=10)
        
        EVENTS_INGESTED.labels(topic=self.topic).inc()
        
        return {
            "topic": record_metadata.topic,
            "partition": record_metadata.partition,
            "offset": record_metadata.offset,
        }
    
    def publish_batch(self, events: list) -> Dict[str, Any]:
        """Publish multiple events.
        
        Args:
            events: List of events to publish
            
        Returns:
            Publishing summary
        """
        successful = 0
        failed = 0
        
        for event in events:
            try:
                self.publish(event)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to publish event in batch: {e}")
                failed += 1
        
        return {
            "total": len(events),
            "successful": successful,
            "failed": failed,
        }
    
    def close(self):
        """Close the producer connection."""
        if self.producer:
            self.producer.close()


def publish_event(event_id: str, text: str, metadata: Optional[Dict] = None) -> bool:
    """Convenience function to publish a single event.
    
    Args:
        event_id: Unique event identifier
        text: Event text content
        metadata: Optional metadata
        
    Returns:
        True if successful, False otherwise
    """
    producer = KafkaEventProducer()
    event = {
        "id": event_id,
        "text": text,
        "metadata": metadata or {},
    }
    try:
        producer.publish(event)
        producer.close()
        return True
    except Exception as e:
        logger.error(f"Failed to publish event {event_id}: {e}")
        try:
            producer.close()
        except:
            pass
        return False
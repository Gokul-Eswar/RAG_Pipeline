"""Kafka/Redpanda messaging client."""

import json
import os
from typing import Dict, Any, Optional

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
            print(f"Failed to create Kafka producer: {e}")
            return None
    
    def publish(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Publish a single event.
        
        Args:
            event: Event dictionary to publish
            
        Returns:
            Kafka metadata or None if failed
        """
        if self.producer is None:
            return None
        
        try:
            future = self.producer.send(self.topic, value=event)
            record_metadata = future.get(timeout=10)
            
            return {
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
            }
        except KafkaError as e:
            print(f"Kafka error: {e}")
            return None
        except Exception as e:
            print(f"Error publishing event: {e}")
            return None
    
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
            result = self.publish(event)
            if result:
                successful += 1
            else:
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
    result = producer.publish(event)
    producer.close()
    return result is not None

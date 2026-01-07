"""Kafka/Redpanda producer for ingesting raw events."""

import json
import os
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError


class EventProducer:
    """Producer for publishing events to Kafka/Redpanda."""
    
    def __init__(self, broker: Optional[str] = None, topic: Optional[str] = None):
        """Initialize the event producer.
        
        Args:
            broker: Kafka broker address (default from env: KAFKA_BROKER)
            topic: Target topic name (default from env: KAFKA_TOPIC_INGESTION)
        """
        self.broker = broker or os.getenv("KAFKA_BROKER", "redpanda:9092")
        self.topic = topic or os.getenv("KAFKA_TOPIC_INGESTION", "raw_events")
        self.producer = KafkaProducer(
            bootstrap_servers=self.broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
    
    def publish_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Publish an event to the Kafka topic.
        
        Args:
            event: Dictionary containing event data
                   Required keys: 'id', 'text'
                   Optional keys: 'metadata', 'timestamp'
                   
        Returns:
            Dictionary with Kafka metadata (topic, partition, offset) or None if failed
        """
        try:
            future = self.producer.send(self.topic, value=event)
            record_metadata = future.get(timeout=10)
            
            return {
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset,
            }
        except KafkaError as e:
            print(f"Error publishing event: {e}")
            return None
    
    def publish_batch(self, events: list) -> Dict[str, Any]:
        """Publish multiple events to Kafka.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Dictionary with summary of successful/failed publishes
        """
        successful = 0
        failed = 0
        
        for event in events:
            result = self.publish_event(event)
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
        self.producer.close()


def publish_event(event_id: str, text: str, metadata: Optional[Dict] = None) -> bool:
    """Convenience function to publish a single event.
    
    Args:
        event_id: Unique identifier for the event
        text: Text content of the event
        metadata: Optional metadata dictionary
        
    Returns:
        True if successful, False otherwise
    """
    producer = EventProducer()
    event = {
        "id": event_id,
        "text": text,
        "metadata": metadata or {},
    }
    result = producer.publish_event(event)
    producer.close()
    return result is not None

"""Event ingestion processing."""

from src.infrastructure.messaging.kafka import KafkaEventProducer, publish_event

__all__ = ["KafkaEventProducer", "publish_event"]

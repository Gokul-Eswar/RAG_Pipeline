"""Kafka/Redpanda messaging consumer."""

import json
import os
import logging
from typing import Dict, Any, Optional, Generator

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
except ImportError:
    KafkaConsumer = None
    KafkaError = None

logger = logging.getLogger(__name__)


class KafkaEventConsumer:
    """Consumer for reading events from Kafka/Redpanda.
    
    Handles event consumption with proper deserialization and error handling.
    """
    
    def __init__(self, broker: Optional[str] = None, topic: Optional[str] = None, group_id: str = "rag_processor_group"):
        """Initialize the event consumer.
        
        Args:
            broker: Kafka broker address
            topic: Target topic name
            group_id: Consumer group ID
        """
        self.broker = broker or os.getenv("KAFKA_BROKER", "redpanda:9092")
        self.topic = topic or os.getenv("KAFKA_TOPIC_INGESTION", "raw_events")
        self.group_id = group_id
        self.consumer = self._create_consumer()
    
    def _create_consumer(self) -> Optional[KafkaConsumer]:
        """Create Kafka consumer instance."""
        if KafkaConsumer is None:
            return None
        try:
            return KafkaConsumer(
                self.topic,
                bootstrap_servers=self.broker,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=False  # We'll commit manually after processing
            )
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            return None
            
    def consume(self) -> Generator[Dict[str, Any], None, None]:
        """Consume messages from the topic.
        
        Yields:
            Decoded message dictionaries
        """
        if not self.consumer:
            logger.error("Kafka consumer not available")
            return
            
        logger.info(f"Starting consumption from {self.topic}...")
        
        try:
            for message in self.consumer:
                try:
                    yield message.value
                    # Manually commit after successful yielding (and processing by caller)
                    self.consumer.commit()
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # In a real app, we might want to DLQ this or pause
        except Exception as e:
            logger.error(f"Consumption error: {e}")

    def consume_batches(self, batch_size: int = 10, timeout_ms: int = 1000) -> Generator[list[Dict[str, Any]], None, None]:
        """Consume messages in batches.
        
        Args:
            batch_size: Max messages per batch
            timeout_ms: Polling timeout
            
        Yields:
            List of message dictionaries
        """
        if not self.consumer:
            logger.error("Kafka consumer not available")
            return

        logger.info(f"Starting batch consumption from {self.topic}...")
        
        try:
            while True:
                # Poll returns a dict of {TopicPartition: [messages]}
                message_batch = self.consumer.poll(timeout_ms=timeout_ms, max_records=batch_size)
                
                if not message_batch:
                    continue
                    
                flattened_batch = []
                for partition_batch in message_batch.values():
                    for message in partition_batch:
                        flattened_batch.append(message.value)
                
                if flattened_batch:
                    yield flattened_batch
                    # Commit the offsets for the whole batch after yielding
                    self.consumer.commit()
                    
        except Exception as e:
            logger.error(f"Batch consumption error: {e}")
            
    def close(self):
        """Close the consumer connection."""
        if self.consumer:
            self.consumer.close()

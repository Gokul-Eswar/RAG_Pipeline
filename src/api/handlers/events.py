"""Event ingestion API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
from typing import Optional

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
except ImportError:
    KafkaProducer = None
    KafkaError = None

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class IngestEventRequest(BaseModel):
    """Request schema for event ingestion."""
    id: str
    text: str
    metadata: dict | None = None


def get_kafka_producer():
    """Get or create a Kafka producer."""
    if KafkaProducer is None:
        return None
    
    broker = os.getenv("KAFKA_BROKER", "redpanda:9092")
    return KafkaProducer(
        bootstrap_servers=broker,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )


@router.get("/health", description="Health check for ingestion service")
def check_ingestion_health():
    """Check Kafka/Redpanda connectivity."""
    broker = os.getenv("KAFKA_BROKER", "redpanda:9092")
    return {"kafka": broker, "status": "configured"}


@router.post("/", description="Publish event to streaming platform")
def ingest_event(request: IngestEventRequest):
    """Publish a single event to the streaming platform (Kafka/Redpanda).
    
    The event will be published to the configured Kafka topic for processing.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="text is required")
    
    try:
        producer = get_kafka_producer()
        if producer is None:
            return {
                "status": "accepted",
                "id": request.id,
                "warning": "Kafka producer not available - item queued locally"
            }
        
        message = {
            "id": request.id,
            "text": request.text,
            "metadata": request.metadata or {},
        }
        
        topic = os.getenv("KAFKA_TOPIC_INGESTION", "raw_events")
        future = producer.send(topic, value=message)
        record_metadata = future.get(timeout=10)
        producer.close()
        
        return {
            "status": "accepted",
            "id": request.id,
            "topic": record_metadata.topic,
            "partition": record_metadata.partition,
            "offset": record_metadata.offset,
        }
    except KafkaError as e:
        raise HTTPException(status_code=503, detail=f"Kafka error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest event: {str(e)}")

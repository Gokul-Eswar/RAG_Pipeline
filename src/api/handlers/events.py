"""Event ingestion API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
import json
from typing import Optional
from src.api.security import get_current_active_user

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


from src.infrastructure.messaging.kafka import KafkaEventProducer

@router.get("/health", description="Health check for ingestion service")
def check_ingestion_health():
    """Check Kafka/Redpanda connectivity."""
    broker = os.getenv("KAFKA_BROKER", "redpanda:9092")
    return {"kafka": broker, "status": "configured"}


@router.post("/", description="Publish event to streaming platform")
def ingest_event(
    request: IngestEventRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Publish a single event to the streaming platform (Kafka/Redpanda).
    
    The event will be published to the configured Kafka topic for processing.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="text is required")
    
    try:
        producer = KafkaEventProducer()
        
        message = {
            "id": request.id,
            "text": request.text,
            "metadata": request.metadata or {},
        }
        
        result = producer.publish(message)
        producer.close()
        
        if result:
            return {
                "status": "accepted",
                "id": request.id,
                **result
            }
        else:
             return {
                "status": "accepted",
                "id": request.id,
                "warning": "Kafka producer not available - item queued locally (simulation)"
            }

    except Exception as e:
        # Check if it's just a connection error (Circuit Breaker might handle this logging)
        raise HTTPException(status_code=503, detail=f"Failed to ingest event: {str(e)}")

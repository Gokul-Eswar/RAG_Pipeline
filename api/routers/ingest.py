from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestItem(BaseModel):
    id: str
    text: str
    metadata: dict | None = None


@router.post("/")
def ingest(item: IngestItem):
    # Placeholder: publish to streaming ingestion (Kafka/Redpanda)
    # Replace with real producer code in `ingestion/`.
    if not item.text:
        raise HTTPException(status_code=400, detail="text is required")
    return {"status": "accepted", "id": item.id}

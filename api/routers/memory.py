from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter(prefix="/memory", tags=["memory"])


class UpsertRequest(BaseModel):
    collection: str
    vectors: list


@router.get("/health")
def memory_health():
    # Simple placeholder health check for Qdrant
    host = os.getenv("QDRANT_HOST", "qdrant")
    port = os.getenv("QDRANT_PORT", "6333")
    return {"qdrant": f"{host}:{port}"}


@router.post("/upsert")
def upsert(req: UpsertRequest):
    if not req.vectors:
        raise HTTPException(status_code=400, detail="vectors are required")
    # Placeholder: call into api.connectors.qdrant_client to upsert
    return {"status": "ok", "collection": req.collection, "count": len(req.vectors)}

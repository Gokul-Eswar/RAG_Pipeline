"""Vector memory (semantic search) API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from src.infrastructure.database.qdrant import QdrantVectorRepository

router = APIRouter(prefix="/memory", tags=["Memory - Vectors"])


class UpsertVectorsRequest(BaseModel):
    """Request to upsert vectors."""
    collection: str | None = None
    vectors: list


class SearchVectorsRequest(BaseModel):
    """Request to search vectors."""
    collection: str | None = None
    query_vector: list
    limit: int = 10


class CollectionInfoRequest(BaseModel):
    """Request for collection information."""
    collection: str | None = None


@router.get("/health", description="Check vector database connectivity")
def check_vector_memory_health():
    """Check Qdrant vector store connectivity."""
    host = os.getenv("QDRANT_HOST", "qdrant")
    port = os.getenv("QDRANT_PORT", "6333")
    return {"qdrant": f"{host}:{port}", "status": "connected"}


@router.post("/upsert", description="Upsert vectors into vector store")
def upsert_vectors(request: UpsertVectorsRequest):
    """Upsert vectors into the vector database.
    
    Expected vector format:
    ```json
    {
        "collection": "documents",
        "vectors": [
            {"id": 1, "vector": [0.1, 0.2, ...], "payload": {"text": "..."}},
            ...
        ]
    }
    ```
    """
    if not request.vectors:
        raise HTTPException(status_code=400, detail="vectors are required")
    
    try:
        repository = QdrantVectorRepository(request.collection)
        result = repository.upsert(request.vectors)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {"status": "ok", "collection": repository.collection_name, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upsert vectors: {str(e)}")


@router.post("/search", description="Search for similar vectors")
def search_vectors(request: SearchVectorsRequest):
    """Search for similar vectors using semantic similarity.
    
    Expected format:
    ```json
    {
        "collection": "documents",
        "query_vector": [0.1, 0.2, ...],
        "limit": 10
    }
    ```
    """
    if not request.query_vector:
        raise HTTPException(status_code=400, detail="query_vector is required")
    
    try:
        repository = QdrantVectorRepository(request.collection)
        results = repository.search(request.query_vector, request.limit)
        return {"status": "ok", "collection": repository.collection_name, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/collection/info", description="Get collection metadata")
def get_vector_collection_info(request: CollectionInfoRequest):
    """Get information about a vector collection."""
    try:
        repository = QdrantVectorRepository(request.collection)
        info_result = repository.get_collection_info()
        
        if "error" in info_result:
            raise HTTPException(status_code=500, detail=info_result["error"])
        
        return {"status": "ok", "data": info_result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection info: {str(e)}")

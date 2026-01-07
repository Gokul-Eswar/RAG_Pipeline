from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from api.connectors.qdrant_client import QdrantVectorStore

router = APIRouter(prefix="/memory", tags=["memory"])


class UpsertRequest(BaseModel):
    collection: str | None = None
    vectors: list


class SearchRequest(BaseModel):
    collection: str | None = None
    query_vector: list
    limit: int = 10


class CollectionInfo(BaseModel):
    collection: str | None = None


@router.get("/health")
def memory_health():
    """Health check for Qdrant vector store."""
    host = os.getenv("QDRANT_HOST", "qdrant")
    port = os.getenv("QDRANT_PORT", "6333")
    return {"qdrant": f"{host}:{port}", "status": "connected"}


@router.post("/upsert")
def upsert(req: UpsertRequest):
    """Upsert vectors into the vector store.
    
    Expected vector format:
    {
        "collection": "documents",
        "vectors": [
            {"id": 1, "vector": [0.1, 0.2, ...], "payload": {"text": "..."}},
            ...
        ]
    }
    """
    if not req.vectors:
        raise HTTPException(status_code=400, detail="vectors are required")
    
    try:
        store = QdrantVectorStore(req.collection)
        result = store.upsert_vectors(req.vectors)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {"status": "ok", "collection": store.collection_name, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upsert vectors: {str(e)}")


@router.post("/search")
def search_vectors(req: SearchRequest):
    """Search for similar vectors.
    
    Expected format:
    {
        "collection": "documents",
        "query_vector": [0.1, 0.2, ...],
        "limit": 10
    }
    """
    if not req.query_vector:
        raise HTTPException(status_code=400, detail="query_vector is required")
    
    try:
        store = QdrantVectorStore(req.collection)
        results = store.search_vectors(req.query_vector, req.limit)
        return {"status": "ok", "collection": store.collection_name, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/collection/info")
def get_collection_info(info: CollectionInfo):
    """Get information about a collection."""
    try:
        store = QdrantVectorStore(info.collection)
        info_result = store.get_collection_info()
        
        if "error" in info_result:
            raise HTTPException(status_code=500, detail=info_result["error"])
        
        return {"status": "ok", "data": info_result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection info: {str(e)}")

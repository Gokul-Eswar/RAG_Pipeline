"""Hybrid retrieval API endpoints."""

import re
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository
from src.ai.models.language_models import SentenceTransformerModel
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/memory/search", tags=["Memory - Hybrid"])

# Initialize embedding model lazily
_embedding_model = None

def get_embedding_model():
    """Get or initialize the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformerModel()
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise HTTPException(status_code=500, detail="Embedding service unavailable")
    return _embedding_model


class HybridSearchRequest(BaseModel):
    """Request for hybrid search."""
    query_text: str
    limit: int = 5
    collection: str | None = None


def extract_keywords(text: str) -> List[str]:
    """Basic keyword extraction from text.
    
    Filters out short words and common stop words (simulated).
    """
    # Simple split and filter
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "are"}
    return [w for w in words if len(w) > 2 and w not in stop_words]


@router.post("/hybrid", description="Perform hybrid search (Vector + Graph)")
def search_hybrid(
    request: HybridSearchRequest,
    model: SentenceTransformerModel = Depends(get_embedding_model)
):
    """Search using both vector similarity and graph relationships.
    
    1. Converts query text to vector using sentence-transformers.
    2. Searches Qdrant for semantically similar items.
    3. Extracts keywords and searches Neo4j for related context.
    4. Combines and returns unified results.
    """
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    start_time = time.time()
    
    # 1. Generate Embedding
    try:
        query_vector = model.embed(request.query_text)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate query embedding")

    # 2. Vector Search (Semantic)
    vector_results = []
    try:
        qdrant = QdrantVectorRepository(request.collection)
        if qdrant.check_connectivity():
            vector_results = qdrant.search(query_vector, request.limit)
        else:
            logger.warning("Qdrant connectivity check failed during hybrid search")
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")

    # 3. Graph Search (Structural/Relational)
    graph_context = []
    keywords = []
    try:
        keywords = extract_keywords(request.query_text)
        if keywords:
            neo4j = Neo4jGraphRepository()
            if neo4j.check_connectivity():
                graph_context = neo4j.query_related_nodes(keywords, limit=request.limit)
            else:
                logger.warning("Neo4j connectivity check failed during hybrid search")
            neo4j.close()
    except Exception as e:
        logger.error(f"Graph search failed: {str(e)}")

    # 4. Combine Results
    # Basic combination: return both sets.
    # In a more advanced implementation, we would use graph context to re-rank vector results
    
    processing_time = time.time() - start_time
    logger.info(
        f"Hybrid search completed in {processing_time:.3f}s",
        extra={
            "query": request.query_text,
            "vector_results_count": len(vector_results),
            "graph_results_count": len(graph_context),
            "keywords": keywords
        }
    )
    
    return {
        "status": "ok",
        "query": request.query_text,
        "results": {
            "semantic": vector_results,
            "structural": graph_context
        },
        "meta": {
            "strategy": "hybrid_v1",
            "processing_time_ms": int(processing_time * 1000),
            "keywords_extracted": keywords,
            "vector_engine": "qdrant",
            "graph_engine": "neo4j"
        }
    }

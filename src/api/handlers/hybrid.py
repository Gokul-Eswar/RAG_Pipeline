"""Hybrid retrieval API endpoints."""

import random
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository

router = APIRouter(prefix="/memory/search", tags=["Memory - Hybrid"])


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
    return [w for w in words if len(w) > 3 and w not in stop_words]


@router.post("/hybrid", description="Perform hybrid search (Vector + Graph)")
def search_hybrid(request: HybridSearchRequest):
    """Search using both vector similarity and graph relationships.
    
    1. Converts query text to vector (currently mocked).
    2. Searches Qdrant for semantically similar items.
    3. Extracts keywords and searches Neo4j for related context.
    4. Combines and returns unified results.
    """
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    # 1. Generate Embedding (Mocked for now)
    # TODO: Integrate with actual LLM service
    vector_dim = 384
    query_vector = [random.uniform(-1.0, 1.0) for _ in range(vector_dim)]

    # 2. Vector Search (Semantic)
    vector_results = []
    try:
        qdrant = QdrantVectorRepository(request.collection)
        if qdrant.check_connectivity():
            vector_results = qdrant.search(query_vector, request.limit)
    except Exception as e:
        print(f"Vector search warning: {str(e)}")

    # 3. Graph Search (Structural/Relational)
    graph_context = []
    try:
        keywords = extract_keywords(request.query_text)
        if keywords:
            neo4j = Neo4jGraphRepository()
            if neo4j.check_connectivity():
                graph_context = neo4j.query_related_nodes(keywords, limit=request.limit)
            neo4j.close()
    except Exception as e:
        print(f"Graph search warning: {str(e)}")

    # 4. Combine Results
    # For now, we return them as separate components in the response
    # In a more advanced implementation, we would use graph context to re-rank vector results
    
    return {
        "status": "ok",
        "query": request.query_text,
        "results": {
            "semantic": vector_results,
            "structural": graph_context
        },
        "meta": {
            "strategy": "hybrid_v1",
            "keywords_extracted": keywords if 'keywords' in locals() else [],
            "vector_engine": "qdrant",
            "graph_engine": "neo4j"
        }
    }

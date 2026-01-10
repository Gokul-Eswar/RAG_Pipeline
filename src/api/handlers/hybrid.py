"""Hybrid retrieval API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import random
import os

from src.infrastructure.database.qdrant import QdrantVectorRepository
from src.infrastructure.database.neo4j import Neo4jGraphRepository

router = APIRouter(prefix="/memory/search", tags=["Memory - Hybrid"])


class HybridSearchRequest(BaseModel):
    """Request for hybrid search."""
    query_text: str
    limit: int = 5
    collection: str | None = None


@router.post("/hybrid", description="Perform hybrid search (Vector + Graph)")
def search_hybrid(request: HybridSearchRequest):
    """Search using both vector similarity and graph relationships.
    
    1. Converts query text to vector (currently mocked).
    2. Searches Qdrant for semantically similar items.
    3. Searches Neo4j for related context (currently mocked).
    """
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    # 1. Generate Embedding (Mocked for now)
    # TODO: Integrate with actual LLM service when available
    # Using 384 dimensions as it's a common default for sentence-transformers
    vector_dim = 384
    query_vector = [random.uniform(-1.0, 1.0) for _ in range(vector_dim)]

    # 2. Vector Search
    vector_results = []
    try:
        qdrant = QdrantVectorRepository(request.collection)
        # Only attempt search if client is available
        if qdrant.check_connectivity():
            vector_results = qdrant.search(query_vector, request.limit)
    except Exception as e:
        # Log error but don't fail the whole request if one part fails?
        # For now, we'll let it pass or maybe raise HTTP 500 if critical
        print(f"Vector search warning: {str(e)}")

    # 3. Graph Search (Mocked/Basic)
    # TODO: Implement actual entity extraction and graph traversal
    graph_context = []
    try:
        neo4j = Neo4jGraphRepository()
        if neo4j.check_connectivity():
            # Future: Extract entities from query_text and find in graph
            # For now, we just return an empty list or mock data
            pass
        neo4j.close()
    except Exception as e:
        print(f"Graph search warning: {str(e)}")

    # 4. Combine Results (Simple concatenation for now)
    # In a real system, we would re-rank or merge based on relevance
    
    return {
        "status": "ok",
        "results": vector_results,
        "vector_matches": vector_results,
        "graph_context": graph_context,
        "meta": {
            "strategy": "hybrid_mock",
            "notes": "Embedding and Graph Linkage are currently mocked pending LLM integration."
        }
    }

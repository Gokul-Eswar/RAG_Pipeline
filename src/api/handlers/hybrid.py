"""Hybrid retrieval API endpoints."""

import re
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository
from src.ai.models.language_models import SentenceTransformerModel, OllamaModel
from src.utils.logging import get_logger
from src.api.security import get_current_active_user

logger = get_logger(__name__)
router = APIRouter(prefix="/memory/search", tags=["Memory - Hybrid"])

# Initialize embedding model lazily
_embedding_model = None
_llm_model = None

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

def get_llm_model():
    """Get or initialize the LLM model."""
    global _llm_model
    if _llm_model is None:
        try:
            _llm_model = OllamaModel()
        except Exception as e:
            logger.error(f"Failed to initialize LLM model: {e}")
            raise HTTPException(status_code=500, detail="LLM service unavailable")
    return _llm_model


class HybridSearchRequest(BaseModel):
    """Request for hybrid search."""
    query_text: str
    limit: int = 5
    collection: str | None = None

class GenerateRequest(BaseModel):
    """Request for RAG generation."""
    query_text: str
    limit: int = 3
    model_name: str = "llama3"
    include_sources: bool = True


def extract_keywords(text: str) -> List[str]:
    """Basic keyword extraction from text.
    
    Filters out short words and common stop words (simulated).
    """
    # Simple split and filter
    words = re.findall(r'\b\w+\b', text.lower())
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "are"}
    return [w for w in words if len(w) > 2 and w not in stop_words]

def perform_hybrid_search(
    query_text: str,
    limit: int,
    model: SentenceTransformerModel
) -> Dict[str, List[Any]]:
    """Internal helper to perform hybrid search."""
    
    # 1. Generate Embedding
    try:
        query_vector = model.embed(query_text)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return {"semantic": [], "structural": []}

    # 2. Vector Search (Semantic)
    vector_results = []
    try:
        qdrant = QdrantVectorRepository()
        if qdrant.check_connectivity():
            vector_results = qdrant.search(query_vector, limit)
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")

    # 3. Graph Search (Structural/Relational)
    graph_context = []
    try:
        keywords = extract_keywords(query_text)
        if keywords:
            neo4j = Neo4jGraphRepository()
            if neo4j.check_connectivity():
                graph_context = neo4j.query_related_nodes(keywords, limit=limit)
            neo4j.close()
    except Exception as e:
        logger.error(f"Graph search failed: {str(e)}")

    return {
        "semantic": vector_results,
        "structural": graph_context
    }


@router.post("/hybrid", description="Perform hybrid search (Vector + Graph)")
def search_hybrid(
    request: HybridSearchRequest,
    model: SentenceTransformerModel = Depends(get_embedding_model),
    current_user: dict = Depends(get_current_active_user)
):
    """Search using both vector similarity and graph relationships."""
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    start_time = time.time()
    
    results = perform_hybrid_search(request.query_text, request.limit, model)
    
    processing_time = time.time() - start_time
    logger.info(
        f"Hybrid search completed in {processing_time:.3f}s",
        extra={
            "query": request.query_text,
            "vector_results_count": len(results["semantic"]),
            "graph_results_count": len(results["structural"])
        }
    )
    
    return {
        "status": "ok",
        "query": request.query_text,
        "results": results,
        "meta": {
            "strategy": "hybrid_v1",
            "processing_time_ms": int(processing_time * 1000),
            "vector_engine": "qdrant",
            "graph_engine": "neo4j"
        }
    }

@router.post("/generate", description="RAG: Generate answer using hybrid context")
def generate_answer(
    request: GenerateRequest,
    embed_model: SentenceTransformerModel = Depends(get_embedding_model),
    llm_model: OllamaModel = Depends(get_llm_model),
    current_user: dict = Depends(get_current_active_user)
):
    """Generate an answer using retrieved context from Vector and Graph DBs.
    
    1. Retrieve context using hybrid search.
    2. Format context for the LLM.
    3. Generate answer using Ollama.
    """
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    start_time = time.time()
    
    # 1. Retrieve Context
    context_data = perform_hybrid_search(request.query_text, request.limit, embed_model)
    
    # 2. Format Context
    context_parts = []
    
    # Add Semantic Context
    for item in context_data.get("semantic", []):
        text = item.payload.get("text", "") if hasattr(item, "payload") else str(item)
        if text:
            context_parts.append(f"- {text}")
            
    # Add Structural Context
    for item in context_data.get("structural", []):
        # Neo4j results are dicts
        props = item.get("n", {})
        name = props.get("name") or props.get("title") or str(props)
        context_parts.append(f"- Entity/Node: {name}")

    context_str = "\n".join(context_parts)
    
    if not context_str:
        context_str = "No specific context found in database."

    # 3. Construct Prompt
    system_prompt = (
        "You are a helpful AI assistant backed by a knowledge base. "
        "Use the provided context to answer the user's question. "
        "If the answer is not in the context, say so politely."
    )
    
    user_prompt = (
        f"Context:\n{context_str}\n\n"
        f"Question: {request.query_text}\n\n"
        f"Answer:"
    )

    # 4. Generate
    try:
        # Update model name if requested
        if request.model_name != llm_model.model_name:
            llm_model.model_name = request.model_name
            
        answer = llm_model.generate(
            prompt=user_prompt,
            system=system_prompt,
            stream=False
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

    processing_time = time.time() - start_time
    
    response = {
        "status": "ok",
        "answer": answer,
        "meta": {
            "model": request.model_name,
            "processing_time_ms": int(processing_time * 1000)
        }
    }
    
    if request.include_sources:
        response["sources"] = context_data

    return response

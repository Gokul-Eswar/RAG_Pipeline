"""Hybrid retrieval API endpoints."""

import re
import time
import hashlib
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository
from src.infrastructure.cache.redis import RedisCache
from src.ai.models.language_models import SentenceTransformerModel, OllamaModel
from src.processing.extraction.nlp import SpacyExtractor, SPACY_AVAILABLE
from src.utils.logging import get_logger
from src.api.security import get_current_active_user

logger = get_logger(__name__)
router = APIRouter(prefix="/memory/search", tags=["Memory - Hybrid"])

# Reusable singletons across requests
_embedding_model: Optional[SentenceTransformerModel] = None
_llm_model: Optional[OllamaModel] = None
_qdrant_repo: Optional[QdrantVectorRepository] = None
_neo4j_repo: Optional[Neo4jGraphRepository] = None
_spacy_extractor: Optional[SpacyExtractor] = None


def get_embedding_model() -> SentenceTransformerModel:
    """Get or initialize the embedding model singleton."""
    global _embedding_model
    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformerModel()
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise HTTPException(status_code=500, detail="Embedding service unavailable")
    return _embedding_model


def get_llm_model() -> OllamaModel:
    """Get or initialize the LLM model singleton."""
    global _llm_model
    if _llm_model is None:
        try:
            _llm_model = OllamaModel()
        except Exception as e:
            logger.error(f"Failed to initialize LLM model: {e}")
            raise HTTPException(status_code=500, detail="LLM service unavailable")
    return _llm_model


def get_qdrant_repo() -> QdrantVectorRepository:
    """Get or initialize the Qdrant repository singleton."""
    global _qdrant_repo
    if _qdrant_repo is None:
        _qdrant_repo = QdrantVectorRepository()
    return _qdrant_repo


def get_neo4j_repo() -> Neo4jGraphRepository:
    """Get or initialize the Neo4j repository singleton."""
    global _neo4j_repo
    if _neo4j_repo is None:
        _neo4j_repo = Neo4jGraphRepository()
    return _neo4j_repo


def get_nlp_extractor() -> Optional[SpacyExtractor]:
    """Get or initialize the spaCy extractor singleton for entity extraction."""
    global _spacy_extractor
    if _spacy_extractor is None and SPACY_AVAILABLE:
        try:
            _spacy_extractor = SpacyExtractor()
        except Exception as e:
            logger.warning(f"Could not load SpacyExtractor: {e}")
            _spacy_extractor = None
    return _spacy_extractor


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


# Comprehensive stop words for fallback entity/keyword extraction
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "let's", "me", "more", "most", "my", "myself", "no", "nor", "not",
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "were", "weren't", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "won't", "would", "you", "your", "yours", "yourself", "yourselves"
}


def extract_search_terms(text: str) -> List[str]:
    """Extract search terms and named entities from query text.
    
    Prefers spaCy Named Entity Recognition when available, falling back
    to filtered tokenization and capitalized phrases.
    """
    terms: List[str] = []
    
    # 1. Try spaCy Named Entity Recognition
    extractor = get_nlp_extractor()
    if extractor and extractor.nlp:
        try:
            entities = extractor.extract_entities(text)
            for ent in entities:
                ent_text = ent.get("text", "").strip()
                if ent_text and ent_text.lower() not in STOP_WORDS:
                    terms.append(ent_text)
        except Exception as e:
            logger.debug(f"Entity extraction skipped: {e}")

    # 2. Extract significant words / multi-word phrases
    words = re.findall(r'\b[A-Za-z0-9_-]+\b', text)
    filtered = [w for w in words if len(w) > 2 and w.lower() not in STOP_WORDS]
    
    for word in filtered:
        if word not in terms and word.lower() not in [t.lower() for t in terms]:
            terms.append(word)

    return terms if terms else [w for w in words if len(w) > 1]


def _serialize_vector_item(item: Any) -> Dict[str, Any]:
    """Ensure vector search items are JSON-serializable."""
    if isinstance(item, dict):
        return item
    serialized: Dict[str, Any] = {}
    if hasattr(item, "id"):
        serialized["id"] = item.id
    if hasattr(item, "score"):
        serialized["score"] = float(item.score)
    if hasattr(item, "payload") and isinstance(item.payload, dict):
        serialized["payload"] = item.payload
    else:
        serialized["payload"] = {"text": str(item)}
    return serialized


def perform_hybrid_search(
    query_text: str,
    limit: int,
    model: SentenceTransformerModel
) -> Dict[str, List[Any]]:
    """Perform hybrid search combining vector embeddings and graph relations with caching."""
    # 0. Check Redis cache first
    cache = RedisCache()
    query_hash = hashlib.md5(f"{query_text.strip().lower()}:{limit}".encode()).hexdigest()
    cache_key = f"rag:hybrid:{query_hash}"
    
    cached = cache.get(cache_key)
    if cached is not None and isinstance(cached, dict):
        logger.debug(f"Cache hit for hybrid search query '{query_text}'")
        return cached

    # 1. Generate Embedding
    try:
        query_vector = model.embed(query_text)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return {"semantic": [], "structural": []}

    # 2. Vector Search (Semantic)
    vector_results: List[Dict[str, Any]] = []
    try:
        qdrant = get_qdrant_repo()
        if qdrant.check_connectivity():
            raw_results = qdrant.search(query_vector, limit)
            vector_results = [_serialize_vector_item(r) for r in raw_results]
    except Exception as e:
        logger.error(f"Vector search failed: {e}")

    # 3. Graph Search (Structural / Relational)
    graph_context: List[Dict[str, Any]] = []
    try:
        search_terms = extract_search_terms(query_text)
        if search_terms:
            neo4j = get_neo4j_repo()
            if neo4j.check_connectivity():
                graph_context = neo4j.query_related_nodes(search_terms, limit=limit)
    except Exception as e:
        logger.error(f"Graph search failed: {e}")

    result_payload = {
        "semantic": vector_results,
        "structural": graph_context
    }

    # 4. Cache search result for 5 minutes (300 seconds)
    cache.set(cache_key, result_payload, ttl=300)

    return result_payload


def _format_context_for_llm(context_data: Dict[str, List[Any]]) -> str:
    """Format combined vector and graph context into a structured prompt."""
    context_parts: List[str] = []

    # Semantic Vector results
    semantic_items = context_data.get("semantic", [])
    if semantic_items:
        context_parts.append("### Relevant Text Excerpts (Vector Search):")
        for i, item in enumerate(semantic_items, start=1):
            text = ""
            if isinstance(item, dict):
                payload = item.get("payload", {})
                text = payload.get("text", "") if isinstance(payload, dict) else str(item)
            elif hasattr(item, "payload") and isinstance(item.payload, dict):
                text = item.payload.get("text", "")
            else:
                text = str(item)

            if text.strip():
                context_parts.append(f"[Source {i}]: {text.strip()}")

    # Structural Knowledge Graph triplets
    structural_items = context_data.get("structural", [])
    if structural_items:
        context_parts.append("\n### Verified Knowledge Graph Relations:")
        for item in structural_items:
            if isinstance(item, dict):
                # Triplets from Neo4j query_related_nodes
                if "source" in item and "target" in item:
                    src_props = item["source"].get("props", {}) if isinstance(item["source"], dict) else {}
                    tgt_props = item["target"].get("props", {}) if isinstance(item["target"], dict) else {}
                    src_name = src_props.get("name") or src_props.get("title") or src_props.get("id") or "Entity"
                    rel_type = item.get("relationship", "RELATED_TO")
                    tgt_name = tgt_props.get("name") or tgt_props.get("title") or tgt_props.get("id") or "Entity"
                    context_parts.append(f"- ({src_name}) -[:{rel_type}]-> ({tgt_name})")
                elif "n" in item:
                    props = item.get("n", {})
                    name = props.get("name") or props.get("title") or str(props)
                    context_parts.append(f"- Entity: {name}")
                elif "props" in item:
                    props = item.get("props", {})
                    name = props.get("name") or props.get("title") or str(props)
                    context_parts.append(f"- Entity: {name}")
                else:
                    context_parts.append(f"- Fact: {item}")

    if not context_parts:
        return "No specific context found in database."

    return "\n".join(context_parts)


@router.post("/hybrid", description="Perform hybrid search (Vector + Graph)")
def search_hybrid(
    request: HybridSearchRequest,
    model: SentenceTransformerModel = Depends(get_embedding_model),
    current_user: dict = Depends(get_current_active_user)
):
    """Search using both vector similarity and graph relationships with Redis caching."""
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
            "strategy": "hybrid_v2_cached",
            "processing_time_ms": int(processing_time * 1000),
            "vector_engine": "qdrant",
            "graph_engine": "neo4j",
            "cache_engine": "redis"
        }
    }


@router.post("/generate", description="RAG: Generate answer using hybrid context")
def generate_answer(
    request: GenerateRequest,
    embed_model: SentenceTransformerModel = Depends(get_embedding_model),
    llm_model: OllamaModel = Depends(get_llm_model),
    current_user: dict = Depends(get_current_active_user)
):
    """Generate an answer using retrieved context from Vector and Graph DBs."""
    if not request.query_text:
        raise HTTPException(status_code=400, detail="query_text is required")

    start_time = time.time()

    # 1. Retrieve Context (with Redis cache check)
    context_data = perform_hybrid_search(request.query_text, request.limit, embed_model)

    # 2. Format Context with structured Knowledge Graph triplets and semantic excerpts
    context_str = _format_context_for_llm(context_data)

    # 3. Construct Grounded Prompt
    system_prompt = (
        "You are an advanced Big Data RAG Intelligence assistant. "
        "Answer the user's question accurately and concisely using ONLY the provided context. "
        "Combine the semantic text excerpts with the structured knowledge graph relations when synthesizing your answer. "
        "Cite sources where applicable using [Source #] or [Graph Fact]. "
        "If the context does not contain enough information to answer the question, state that you do not have sufficient information."
    )

    user_prompt = (
        f"Context:\n{context_str}\n\n"
        f"Question: {request.query_text}\n\n"
        f"Answer:"
    )

    # 4. Generate
    try:
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

"""Unit tests for hybrid retrieval handler."""

import pytest
from unittest.mock import MagicMock, patch

from src.api.handlers.hybrid import (
    extract_search_terms,
    _format_context_for_llm,
    perform_hybrid_search,
    _serialize_vector_item
)


def test_extract_search_terms():
    """Test extracting search terms filtering stop words."""
    query = "What is the relationship between Apple and Google?"
    terms = extract_search_terms(query)
    
    assert "Apple" in terms
    assert "Google" in terms
    assert "relationship" in terms
    assert "what" not in [t.lower() for t in terms]
    assert "the" not in [t.lower() for t in terms]
    assert "and" not in [t.lower() for t in terms]


def test_format_context_triplets():
    """Test that Knowledge Graph triplets are properly formatted for LLM."""
    context_data = {
        "semantic": [
            {"payload": {"text": "Apple is a technology company."}},
            {"payload": {"text": "Google operates a search engine."}}
        ],
        "structural": [
            {
                "source": {"props": {"name": "Apple"}},
                "relationship": "COMPETES_WITH",
                "target": {"props": {"name": "Google"}}
            }
        ]
    }
    
    formatted = _format_context_for_llm(context_data)
    
    # Check vector sources
    assert "[Source 1]: Apple is a technology company." in formatted
    assert "[Source 2]: Google operates a search engine." in formatted
    
    # Check graph triplets (verifies the bug fix)
    assert "- (Apple) -[:COMPETES_WITH]-> (Google)" in formatted


def test_format_context_empty():
    """Test formatting when no context is found."""
    formatted = _format_context_for_llm({"semantic": [], "structural": []})
    assert formatted == "No specific context found in database."


def test_serialize_vector_item():
    """Test vector serialization helper."""
    # From dict
    dict_item = {"id": 1, "score": 0.95, "payload": {"text": "hello"}}
    assert _serialize_vector_item(dict_item) == dict_item
    
    # From object with attributes
    class MockPoint:
        id = "point-1"
        score = 0.88
        payload = {"text": "world"}
        
    serialized = _serialize_vector_item(MockPoint())
    assert serialized["id"] == "point-1"
    assert serialized["score"] == 0.88
    assert serialized["payload"]["text"] == "world"


@patch("src.api.handlers.hybrid.RedisCache")
@patch("src.api.handlers.hybrid.get_qdrant_repo")
@patch("src.api.handlers.hybrid.get_neo4j_repo")
def test_perform_hybrid_search_caching(mock_get_neo4j, mock_get_qdrant, mock_redis_cls):
    """Test that hybrid search checks and populates Redis cache."""
    mock_cache = MagicMock()
    mock_redis_cls.return_value = mock_cache
    
    # Simulate cache miss first
    mock_cache.get.return_value = None
    
    # Mock Qdrant
    mock_qdrant = MagicMock()
    mock_qdrant.check_connectivity.return_value = True
    mock_qdrant.search.return_value = [{"payload": {"text": "result1"}}]
    mock_get_qdrant.return_value = mock_qdrant
    
    # Mock Neo4j
    mock_neo4j = MagicMock()
    mock_neo4j.check_connectivity.return_value = True
    mock_neo4j.query_related_nodes.return_value = [
        {"source": {"props": {"name": "A"}}, "relationship": "REL", "target": {"props": {"name": "B"}}}
    ]
    mock_get_neo4j.return_value = mock_neo4j
    
    mock_embed_model = MagicMock()
    mock_embed_model.embed.return_value = [0.1, 0.2, 0.3]
    
    results = perform_hybrid_search("Test query", limit=2, model=mock_embed_model)
    
    assert len(results["semantic"]) == 1
    assert len(results["structural"]) == 1
    # Verify cached
    mock_cache.set.assert_called_once()

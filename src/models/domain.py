"""Data models and schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class Event(BaseModel):
    """Event domain model."""
    id: str
    text: str
    metadata: Optional[dict] = None


class VectorData(BaseModel):
    """Vector data model."""
    id: int
    vector: list = Field(..., description="Embedding vector")
    payload: Optional[dict] = None


class GraphNode(BaseModel):
    """Graph node model."""
    id: int
    label: str
    properties: dict


class GraphRelationship(BaseModel):
    """Graph relationship model."""
    id: int
    type: str
    from_id: int
    to_id: int
    properties: Optional[dict] = None


__all__ = ["Event", "VectorData", "GraphNode", "GraphRelationship"]

"""Graph database API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.api.security import get_current_active_user

router = APIRouter(prefix="/graph", tags=["Memory - Graph"])


class NodeCreateRequest(BaseModel):
    """Request to create a node."""
    label: str
    properties: dict


class RelationshipCreateRequest(BaseModel):
    """Request to create a relationship."""
    from_id: int
    relationship_type: str
    to_id: int
    properties: dict | None = None


class NodeQueryRequest(BaseModel):
    """Request to query a node."""
    label: str
    properties: dict


@router.get("/health", description="Check graph database connectivity")
def check_graph_health():
    """Check Neo4j graph database connectivity."""
    host = os.getenv("NEO4J_HOST", "neo4j")
    return {"neo4j": host, "status": "connected"}


@router.post("/node", description="Create a node in the graph")
def create_graph_node(
    request: NodeCreateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new node in the graph database."""
    if not request.label:
        raise HTTPException(status_code=400, detail="label required")
    
    try:
        repository = Neo4jGraphRepository()
        result = repository.create_node(request.label, request.properties)
        repository.close()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {"status": "created", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")


@router.post("/relationship", description="Create a relationship between nodes")
def create_graph_relationship(
    request: RelationshipCreateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a relationship between two nodes."""
    if not request.relationship_type:
        raise HTTPException(status_code=400, detail="relationship_type required")
    
    try:
        repository = Neo4jGraphRepository()
        result = repository.create_relationship(
            request.from_id, 
            request.relationship_type, 
            request.to_id, 
            request.properties
        )
        repository.close()
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {"status": "created", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create relationship: {str(e)}")


@router.post("/node/find", description="Find a node by properties")
def find_graph_node(
    request: NodeQueryRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Find a node by label and properties."""
    try:
        repository = Neo4jGraphRepository()
        result = repository.find_node(request.label, request.properties)
        repository.close()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return {"status": "found", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find node: {str(e)}")


@router.delete("/node/{node_id}", description="Delete a node by ID")
def delete_graph_node(
    node_id: int,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a node from the graph by ID."""
    try:
        repository = Neo4jGraphRepository()
        success = repository.delete_node(node_id)
        repository.close()
        
        if not success:
            raise HTTPException(status_code=404, detail="Node not found or already deleted")
        
        return {"status": "deleted", "node_id": node_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")

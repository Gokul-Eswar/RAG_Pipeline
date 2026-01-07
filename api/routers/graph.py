from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter(prefix="/graph", tags=["graph"])


class NodeCreate(BaseModel):
    label: str
    properties: dict


@router.get("/health")
def graph_health():
    host = os.getenv("NEO4J_HOST", "neo4j")
    return {"neo4j": host}


@router.post("/node")
def create_node(node: NodeCreate):
    if not node.label:
        raise HTTPException(status_code=400, detail="label required")
    # Placeholder: call into api.connectors.neo4j_client to persist node
    return {"status": "created", "label": node.label}

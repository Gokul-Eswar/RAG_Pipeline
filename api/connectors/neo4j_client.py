import os
from typing import Optional, Dict, Any, List

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - optional dependency during early dev
    GraphDatabase = None


def get_neo4j_driver():
    if GraphDatabase is None:
        return None
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    auth = os.getenv("NEO4J_AUTH", "neo4j/test").split("/")
    user = auth[0]
    pwd = auth[1] if len(auth) > 1 else "test"
    return GraphDatabase.driver(uri, auth=(user, pwd))


class Neo4jClient:
    """Client for Neo4j graph database operations."""
    
    def __init__(self):
        self.driver = get_neo4j_driver()
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new node in the graph database.
        
        Args:
            label: The node label (e.g., 'Entity', 'Document')
            properties: Dictionary of node properties
            
        Returns:
            Dictionary with node ID and properties
        """
        if self.driver is None:
            return {"error": "Neo4j driver not available"}
        
        with self.driver.session() as session:
            props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
            query = f"CREATE (n:{label} {{{props_str}}}) RETURN id(n) AS node_id, properties(n) AS props"
            result = session.run(query, **properties)
            record = result.single()
            if record:
                return {"node_id": record["node_id"], "properties": record["props"]}
            return {"error": "Failed to create node"}
    
    def create_relationship(self, from_id: int, rel_type: str, to_id: int, properties: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a relationship between two nodes.
        
        Args:
            from_id: ID of source node
            rel_type: Type of relationship
            to_id: ID of target node
            properties: Optional relationship properties
            
        Returns:
            Dictionary with relationship details
        """
        if self.driver is None:
            return {"error": "Neo4j driver not available"}
        
        props = properties or {}
        props_str = ", ".join([f"{k}: ${k}" for k in props.keys()]) if props else ""
        rel_props = f" {{{props_str}}}" if props_str else ""
        
        with self.driver.session() as session:
            query = f"MATCH (a), (b) WHERE id(a) = $from_id AND id(b) = $to_id CREATE (a)-[r:{rel_type}{rel_props}]->(b) RETURN id(r) AS rel_id"
            result = session.run(query, from_id=from_id, to_id=to_id, **props)
            record = result.single()
            if record:
                return {"relationship_id": record["rel_id"], "type": rel_type}
            return {"error": "Failed to create relationship"}
    
    def find_node(self, label: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a node matching the given label and properties.
        
        Args:
            label: The node label
            properties: Properties to match
            
        Returns:
            Node data or None if not found
        """
        if self.driver is None:
            return None
        
        with self.driver.session() as session:
            props_str = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
            query = f"MATCH (n:{label}) WHERE {props_str} RETURN id(n) AS node_id, properties(n) AS props LIMIT 1"
            result = session.run(query, **properties)
            record = result.single()
            if record:
                return {"node_id": record["node_id"], "properties": record["props"]}
            return None
    
    def delete_node(self, node_id: int) -> bool:
        """Delete a node by ID.
        
        Args:
            node_id: ID of node to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.driver is None:
            return False
        
        with self.driver.session() as session:
            result = session.run("MATCH (n) WHERE id(n) = $id DETACH DELETE n", id=node_id)
            return result.summary.counters.nodes_deleted > 0
    
    def close(self):
        """Close the driver connection."""
        if self.driver:
            self.driver.close()

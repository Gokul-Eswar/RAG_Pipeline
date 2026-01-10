"""Neo4j graph database repository."""

import os
from typing import Optional, Dict, Any

try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None


class Neo4jGraphRepository:
    """Repository for Neo4j graph database operations.
    
    Provides an abstraction layer for creating, querying, and managing
    nodes and relationships in the graph database.
    """
    
    def __init__(self):
        """Initialize the graph repository with Neo4j driver."""
        self.driver = self._get_driver()
    
    @staticmethod
    def _get_driver():
        """Get or create Neo4j driver instance."""
        if GraphDatabase is None:
            return None
        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        auth_str = os.getenv("NEO4J_AUTH", "neo4j/test")
        auth = auth_str.split("/")
        user = auth[0]
        password = auth[1] if len(auth) > 1 else "test"
        return GraphDatabase.driver(uri, auth=(user, password))
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new node in the graph.
        
        Args:
            label: Node label/type (e.g., 'Document', 'Entity')
            properties: Node properties dictionary
            
        Returns:
            Dictionary with node_id and properties, or error dict
        """
        if self.driver is None:
            return {"error": "Neo4j driver not available"}
        
        try:
            with self.driver.session() as session:
                props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
                query = f"CREATE (n:{label} {{{props_str}}}) RETURN id(n) AS node_id, properties(n) AS props"
                result = session.run(query, **properties)
                record = result.single()
                if record:
                    return {"node_id": record["node_id"], "properties": record["props"]}
                return {"error": "Failed to create node"}
        except Exception as e:
            return {"error": str(e)}
    
    def create_relationship(
        self,
        from_id: int,
        rel_type: str,
        to_id: int,
        properties: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Create a relationship between two nodes.
        
        Args:
            from_id: Source node ID
            rel_type: Relationship type
            to_id: Target node ID
            properties: Optional relationship properties
            
        Returns:
            Dictionary with relationship details, or error dict
        """
        if self.driver is None:
            return {"error": "Neo4j driver not available"}
        
        try:
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
        except Exception as e:
            return {"error": str(e)}
    
    def find_node(self, label: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a node matching given criteria.
        
        Args:
            label: Node label to search
            properties: Properties to match
            
        Returns:
            Node data dict or None if not found
        """
        if self.driver is None:
            return None
        
        try:
            with self.driver.session() as session:
                props_str = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
                query = f"MATCH (n:{label}) WHERE {props_str} RETURN id(n) AS node_id, properties(n) AS props LIMIT 1"
                result = session.run(query, **properties)
                record = result.single()
                if record:
                    return {"node_id": record["node_id"], "properties": record["props"]}
                return None
        except Exception:
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
        
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (n) WHERE id(n) = $id DETACH DELETE n", id=node_id)
                return result.summary.counters.nodes_deleted > 0
        except Exception:
            return False
    
    def check_connectivity(self) -> bool:
        """Check if Neo4j is connected.
        
        Returns:
            True if connected, False otherwise
        """
        if self.driver is None:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                return result.single()[0] == 1
        except Exception:
            return False

    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()

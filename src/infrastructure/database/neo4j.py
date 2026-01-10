"""Neo4j graph database repository."""

import os
from typing import Optional, Dict, Any
from src.utils.config import Config
from src.utils.resilience import get_retry_decorator, get_circuit_breaker
from neo4j.exceptions import ServiceUnavailable, TransientError

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
        uri = Config.NEO4J_URI
        auth_str = Config.NEO4J_AUTH
        auth = auth_str.split("/")
        user = auth[0]
        password = auth[1] if len(auth) > 1 else ""
        return GraphDatabase.driver(
            uri, 
            auth=(user, password),
            connection_timeout=Config.NEO4J_TIMEOUT
        )
    
    @get_circuit_breaker(name="neo4j_create_node")
    @get_retry_decorator(exceptions=(ServiceUnavailable, TransientError))
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
            # Let retry/circuit breaker handle connectivity issues
            if isinstance(e, (ServiceUnavailable, TransientError)):
                raise
            return {"error": str(e)}
    
    @get_circuit_breaker(name="neo4j_create_relationship")
    @get_retry_decorator(exceptions=(ServiceUnavailable, TransientError))
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
            if isinstance(e, (ServiceUnavailable, TransientError)):
                raise
            return {"error": str(e)}
    
    @get_circuit_breaker(name="neo4j_find_node")
    @get_retry_decorator(exceptions=(ServiceUnavailable, TransientError))
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
        except Exception as e:
            if isinstance(e, (ServiceUnavailable, TransientError)):
                raise
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
    
    def query_related_nodes(self, keywords: list[str], limit: int = 5) -> list[dict[str, Any]]:
        """Search for nodes matching keywords and their immediate neighbors.
        
        Args:
            keywords: List of strings to search for in node properties
            limit: Maximum number of primary nodes to find
            
        Returns:
            List of dictionaries containing node and relationship data
        """
        if self.driver is None or not keywords:
            return []
        
        try:
            with self.driver.session() as session:
                # Basic full-text/contains search across all labels and common properties
                # In a production system, you'd use a Full-Text Index
                query = """
                UNWIND $keywords AS keyword
                MATCH (n)
                WHERE any(prop IN keys(n) WHERE n[prop] CONTAINS keyword)
                WITH n LIMIT $limit
                MATCH (n)-[r]-(m)
                RETURN 
                    id(n) AS source_id, 
                    labels(n) AS source_labels, 
                    properties(n) AS source_props,
                    type(r) AS rel_type,
                    id(m) AS target_id,
                    labels(m) AS target_labels,
                    properties(m) AS target_props
                LIMIT 20
                """
                result = session.run(query, keywords=keywords, limit=limit)
                
                context = []
                for record in result:
                    context.append({
                        "source": {"id": record["source_id"], "labels": record["source_labels"], "props": record["source_props"]},
                        "relationship": record["rel_type"],
                        "target": {"id": record["target_id"], "labels": record["target_labels"], "props": record["target_props"]}
                    })
                return context
        except Exception as e:
            print(f"Neo4j query error: {e}")
            return []

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

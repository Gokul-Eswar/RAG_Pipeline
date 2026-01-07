"""Qdrant vector database repository."""

import os
from typing import Optional, Dict, Any, List

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance
except Exception:
    QdrantClient = None
    PointStruct = None
    VectorParams = None
    Distance = None


class QdrantVectorRepository:
    """Repository for Qdrant vector database operations.
    
    Provides an abstraction layer for managing vector embeddings
    and performing semantic searches.
    """
    
    def __init__(self, collection_name: str = None):
        """Initialize the vector repository.
        
        Args:
            collection_name: Name of vector collection (default from env)
        """
        self.client = self._get_client()
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_DEFAULT", "documents")
    
    @staticmethod
    def _get_client() -> Optional[QdrantClient]:
        """Get Qdrant client instance."""
        if QdrantClient is None:
            return None
        host = os.getenv("QDRANT_HOST", "qdrant")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        return QdrantClient(url=f"http://{host}:{port}")
    
    def create_collection(self, vector_size: int = 384, distance_metric: str = "cosine") -> bool:
        """Create a new vector collection.
        
        Args:
            vector_size: Dimensionality of vectors
            distance_metric: Distance metric (cosine, euclidean, manhattan)
            
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False
        
        try:
            distance_map = {
                "cosine": Distance.COSINE,
                "euclidean": Distance.EUCLID,
                "manhattan": Distance.MANHATTAN,
            }
            distance = distance_map.get(distance_metric.lower(), Distance.COSINE)
            
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    def upsert(self, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Insert or update vectors in the collection.
        
        Args:
            vectors: List of vector objects with id, vector, and optional payload
            
        Returns:
            Status dictionary
        """
        if self.client is None:
            return {"error": "Qdrant client not available"}
        
        try:
            points = []
            for item in vectors:
                point = PointStruct(
                    id=item["id"],
                    vector=item["vector"],
                    payload=item.get("payload", {}),
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            return {"status": "ok", "count": len(vectors)}
        except Exception as e:
            return {"error": str(e)}
    
    def search(self, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of search results with scores
        """
        if self.client is None:
            return []
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
            )
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            print(f"Error searching vectors: {e}")
            return []
    
    def delete(self, ids: List[int]) -> bool:
        """Delete vectors by IDs.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=ids,
            )
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metadata and statistics.
        
        Returns:
            Collection information dictionary
        """
        if self.client is None:
            return {"error": "Qdrant client not available"}
        
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": getattr(info, "vectors_count", "N/A"),
                "config": str(info.config) if hasattr(info, "config") else "N/A",
            }
        except Exception as e:
            return {"error": str(e)}

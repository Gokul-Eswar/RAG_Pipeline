"""Qdrant vector database repository."""

import os
import time
from typing import Optional, Dict, Any, List
from src.utils.config import Config
from src.utils.resilience import get_retry_decorator, get_circuit_breaker
from src.utils.metrics import DB_OPERATION_LATENCY
from src.infrastructure.cache.redis import cache_result

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
        self.collection_name = collection_name or Config.QDRANT_COLLECTION
    
    @staticmethod
    def _get_client() -> Optional[QdrantClient]:
        """Get Qdrant client instance."""
        if QdrantClient is None:
            return None
        host = Config.QDRANT_HOST
        port = Config.QDRANT_PORT
        # Qdrant client handles timeouts differently, often passed in methods
        # but we can set a global timeout if the client supports it
        return QdrantClient(url=f"http://{host}:{port}", timeout=Config.QDRANT_TIMEOUT)
    
    @get_retry_decorator()
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
            raise e
    
    @get_circuit_breaker(name="qdrant_upsert")
    @get_retry_decorator()
    def upsert(self, vectors: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, Any]:
        """Insert or update vectors in the collection.
        
        Args:
            vectors: List of vector objects with id, vector, and optional payload
            batch_size: Number of vectors to upsert in one request
            
        Returns:
            Status dictionary
        """
        if self.client is None:
            return {"error": "Qdrant client not available"}
        
        start_time = time.time()
        total_upserted = 0
        
        try:
            # Process in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                points = []
                for item in batch:
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
                total_upserted += len(batch)
                
            return {"status": "ok", "count": total_upserted}
        except Exception as e:
            # Re-raise for retry logic unless it's a structural error
            raise e
        finally:
            DB_OPERATION_LATENCY.labels(database="qdrant", operation="upsert").observe(time.time() - start_time)
    
    @cache_result(ttl=3600)
    @get_circuit_breaker(name="qdrant_search")
    @get_retry_decorator()
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
        
        start_time = time.time()
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
            ).points
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            # Re-raise for retry logic
            raise e
        finally:
            DB_OPERATION_LATENCY.labels(database="qdrant", operation="search").observe(time.time() - start_time)
    
    @get_circuit_breaker(name="qdrant_delete")
    @get_retry_decorator()
    def delete(self, ids: List[int]) -> bool:
        """Delete vectors by IDs.
        
        Args:
            ids: List of vector IDs to delete
            
        Returns:
            True if successful
            
        Raises:
            Exception: If deletion fails
        """
        if self.client is None:
            return False
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids,
        )
        return True
    
    def check_connectivity(self) -> bool:
        """Check if Qdrant is connected.
        
        Returns:
            True if connected, False otherwise
        """
        if self.client is None:
            return False
        
        try:
            # Simple check by getting collections list
            self.client.get_collections()
            return True
        except Exception:
            return False

    @cache_result(ttl=300)
    @get_circuit_breaker(name="qdrant_info")
    @get_retry_decorator()
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
             # Re-raise for retry logic
            raise e
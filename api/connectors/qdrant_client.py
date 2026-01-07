import os
from typing import Optional

try:
    from qdrant_client import QdrantClient
except Exception:  # pragma: no cover - optional dependency during early dev
    QdrantClient = None


def get_qdrant_client() -> Optional[QdrantClient]:
    if QdrantClient is None:
        return None
    host = os.getenv("QDRANT_HOST", "qdrant")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    return QdrantClient(url=f"http://{host}:{port}")

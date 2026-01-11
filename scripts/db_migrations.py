"""Database migration script."""

import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.database.neo4j import Neo4jGraphRepository  # noqa: E402
from src.utils.logging import setup_logging  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)


def apply_neo4j_indexes():
    """Apply Neo4j indexes."""
    logger.info("Applying Neo4j indexes...")
    repo = Neo4jGraphRepository()

    if not repo.check_connectivity():
        logger.error("Failed to connect to Neo4j. Skipping indexes.")
        return

    indexes = [
        "CREATE INDEX entity_id_index IF NOT EXISTS FOR (n:Entity) ON (n.id)",
        "CREATE INDEX entity_type_index IF NOT EXISTS FOR (n:Entity) ON (n.type)",
        "CREATE INDEX document_created_at_index IF NOT EXISTS FOR (n:Document) ON (n.created_at)",  # noqa: E501
        "CREATE INDEX document_id_index IF NOT EXISTS FOR (n:Document) ON (n.id)"  # noqa: E501
    ]

    for query in indexes:
        try:
            logger.info(f"Executing: {query}")
            repo.query_with_timeout(query)
            logger.info("Success.")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")

    repo.close()


if __name__ == "__main__":
    apply_neo4j_indexes()

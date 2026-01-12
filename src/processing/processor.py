"""Document processing pipeline."""

import logging
import uuid
from typing import Dict, Any, List, Optional

from src.processing.extraction.nlp import SpacyExtractor
from src.ai.models.language_models import SentenceTransformerModel
from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates the processing of documents: NLP -> Embed -> Store."""

    def __init__(self):
        """Initialize the processor with necessary components."""
        self.nlp = SpacyExtractor()
        
        # Initialize lazily or handle errors if models/DBs are down
        try:
            self.embedder = SentenceTransformerModel()
        except Exception as e:
            logger.warning(f"Embedding model not available: {e}")
            self.embedder = None
            
        self.graph_repo = Neo4jGraphRepository()
        self.vector_repo = QdrantVectorRepository()

    def process(self, doc_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a single document.

        Args:
            doc_id: Unique identifier for the document
            text: Content of the document
            metadata: Additional metadata

        Returns:
            Dict containing processing summary
        """
        if not doc_id:
            doc_id = str(uuid.uuid4())
        
        logger.info(f"Processing document {doc_id}")
        
        results = {
            "id": doc_id,
            "steps": {
                "nlp": "skipped",
                "vector": "skipped",
                "graph": "skipped"
            },
            "errors": []
        }

        # 1. NLP Extraction
        entities = []
        relations = []
        try:
            entities = self.nlp.extract_entities(text)
            relations = self.nlp.extract_relations(text)
            results["steps"]["nlp"] = "success"
            results["entities_count"] = len(entities)
            results["relations_count"] = len(relations)
        except Exception as e:
            logger.error(f"NLP extraction failed: {e}")
            results["errors"].append(f"NLP: {str(e)}")

        # 2. Vector Embedding & Storage
        if self.embedder:
            try:
                embedding = self.embedder.embed(text)
                
                # Metadata to store with vector
                payload = {
                    "text": text,  # Store chunks in real app
                    "source": "ingest_pipeline",
                    **(metadata or {})
                }
                
                if self.vector_repo.check_connectivity():
                    # Upsert single item
                    self.vector_repo.upsert(
                        collection_name="documents",
                        vectors=[embedding],
                        payloads=[payload],
                        ids=[doc_id]
                    )
                    results["steps"]["vector"] = "success"
                else:
                    results["errors"].append("Vector DB unavailable")
            except Exception as e:
                logger.error(f"Vector processing failed: {e}")
                results["errors"].append(f"Vector: {str(e)}")

        # 3. Graph Storage
        try:
            if self.graph_repo.check_connectivity():
                # Create main document node
                self.graph_repo.create_node("Document", {"id": doc_id, "text_preview": text[:50]})
                
                # Store Entities
                for ent in entities:
                    # Create Entity node (merge to avoid duplicates)
                    # Label = capitalized entity label (e.g., "Person", "Org")
                    label = ent['label'].capitalize()
                    name = ent['text']
                    self.graph_repo.create_node(label, {"name": name})
                    
                    # Link Document -> Entity (MENTIONS)
                    self.graph_repo.create_relationship(
                        "Document", {"id": doc_id},
                        label, {"name": name},
                        "MENTIONS"
                    )

                # Store Relations (Subject -> Verb -> Object)
                for rel in relations:
                    head_name = rel['head']
                    tail_name = rel['tail']
                    rel_type = rel['type'].upper()
                    
                    # We assume nodes exist or we create placeholders (simple approach)
                    # In a real app, we'd be more careful about resolution
                    self.graph_repo.create_node("Entity", {"name": head_name})
                    self.graph_repo.create_node("Entity", {"name": tail_name})
                    
                    self.graph_repo.create_relationship(
                        "Entity", {"name": head_name},
                        "Entity", {"name": tail_name},
                        rel_type
                    )

                results["steps"]["graph"] = "success"
            else:
                 results["errors"].append("Graph DB unavailable")
        except Exception as e:
            logger.error(f"Graph processing failed: {e}")
            results["errors"].append(f"Graph: {str(e)}")
            
        return results

    def close(self):
        """Clean up resources."""
        self.graph_repo.close()

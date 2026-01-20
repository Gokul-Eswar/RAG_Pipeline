"""Document processing pipeline."""

import logging
import uuid
from typing import Dict, Any, List, Optional

from src.processing.extraction.nlp import SpacyExtractor, TransformerExtractor, TRANSFORMERS_AVAILABLE
from src.ai.models.language_models import SentenceTransformerModel
from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates the processing of documents: NLP -> Embed -> Store."""

    def __init__(self):
        """Initialize the processor with necessary components."""
        self.nlp = None
        # Try to load high-performance model first
        if TRANSFORMERS_AVAILABLE:
            try:
                logger.info("Initializing TransformerExtractor (Sports Mode)...")
                self.nlp = TransformerExtractor(sports_mode=True)
            except Exception as e:
                logger.warning(f"Failed to load TransformerExtractor: {e}")
        
        if not self.nlp:
            logger.info("Using SpacyExtractor as NLP backend.")
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
        
        # Reuse batch logic for consistency, even for single item
        results = self.process_batch([{"id": doc_id, "text": text, "metadata": metadata or {}}])
        return results[0] if results else {"id": doc_id, "errors": ["Batch processing returned empty"]}

    def process_batch(self, batch_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of documents efficiently.
        
        Args:
            batch_data: List of dicts, each containing 'id', 'text', 'metadata'
            
        Returns:
            List of result dicts
        """
        if not batch_data:
            return []
            
        logger.info(f"Processing batch of {len(batch_data)} documents")
        
        # Initialize results structure
        results_map = {
            item.get("id", str(uuid.uuid4())): {
                "id": item.get("id", str(uuid.uuid4())),
                "steps": {"nlp": "pending", "vector": "pending", "graph": "pending"},
                "errors": []
            }
            for item in batch_data
        }
        
        # Extract lists for batch ops
        ids = [r["id"] for r in results_map.values()]
        texts = [item.get("text", "") for item in batch_data]
        metadatas = [item.get("metadata", {}) for item in batch_data]
        
        # 1. Batch NLP Extraction
        # Note: Entities extraction is usually per-doc in Spacy, but we can parallelize or loop.
        # TransformerExtractor usually does relations. We'll focus on relations for batching.
        try:
            # We use extract_relations_batch which is optimized in TransformerExtractor
            batch_relations = self.nlp.extract_relations_batch(texts)
            
            # Entities: TransformerExtractor.extract_entities calls extract_relations anyway.
            # For Spacy, we iterate.
            batch_entities = []
            for text in texts:
                batch_entities.append(self.nlp.extract_entities(text))
                
            for i, doc_id in enumerate(ids):
                results_map[doc_id]["steps"]["nlp"] = "success"
                results_map[doc_id]["relations_count"] = len(batch_relations[i])
                results_map[doc_id]["entities_count"] = len(batch_entities[i])
                
        except Exception as e:
            logger.error(f"Batch NLP failed: {e}")
            for doc_id in ids:
                results_map[doc_id]["errors"].append(f"NLP: {str(e)}")
            # Continue to next steps (Vector/Graph might still work without extracted entities)
            batch_relations = [[]] * len(ids)
            batch_entities = [[]] * len(ids)

        # 2. Batch Vector Embedding & Storage
        if self.embedder:
            try:
                embeddings = self.embedder.embed_batch(texts)
                
                payloads = []
                for i, text in enumerate(texts):
                    payloads.append({
                        "text": text[:1000], # Truncate for storage if needed
                        "source": "ingest_pipeline",
                        **(metadatas[i])
                    })
                
                if self.vector_repo.check_connectivity():
                    self.vector_repo.upsert(
                        collection_name="documents",
                        vectors=embeddings,
                        payloads=payloads,
                        ids=ids
                    )
                    for doc_id in ids:
                        results_map[doc_id]["steps"]["vector"] = "success"
                else:
                    for doc_id in ids:
                        results_map[doc_id]["errors"].append("Vector DB unavailable")
            except Exception as e:
                logger.error(f"Batch Vector failed: {e}")
                for doc_id in ids:
                    results_map[doc_id]["errors"].append(f"Vector: {str(e)}")

        # 3. Batch Graph Storage
        try:
            if self.graph_repo.check_connectivity():
                # Prepare Nodes
                doc_nodes = []
                entity_nodes = [] # List of props
                relationships = []
                
                for i, doc_id in enumerate(ids):
                    # Document Node
                    doc_nodes.append({"id": doc_id, "text_preview": texts[i][:50]})
                    
                    # Entity Nodes & Mentions
                    seen_entities = set()
                    for ent in batch_entities[i]:
                        name = ent['text']
                        label = ent['label'].capitalize()
                        if (name, label) not in seen_entities:
                            entity_nodes.append({"name": name, "_label": label}) # Special key _label for grouping
                            seen_entities.add((name, label))
                            
                        # Document -> Entity
                        relationships.append({
                            "from_label": "Document", "from_props": {"id": doc_id},
                            "to_label": label, "to_props": {"name": name},
                            "type": "MENTIONS", "props": {}
                        })
                        
                    # Semantic Relations
                    for rel in batch_relations[i]:
                        head = rel['head']
                        tail = rel['tail']
                        rtype = rel['type'].upper().replace(" ", "_")
                        
                        # Ensure entities exist (simple approach)
                        entity_nodes.append({"name": head, "_label": "Entity"})
                        entity_nodes.append({"name": tail, "_label": "Entity"})
                        
                        relationships.append({
                            "from_label": "Entity", "from_props": {"name": head},
                            "to_label": "Entity", "to_props": {"name": tail},
                            "type": rtype, "props": {}
                        })

                # Execute Batch Writes
                # 1. Documents
                self.graph_repo.batch_create_nodes("Document", doc_nodes)
                
                # 2. Entities (Group by label)
                entities_by_label = {}
                for node in entity_nodes:
                    lbl = node.pop("_label", "Entity")
                    if lbl not in entities_by_label:
                        entities_by_label[lbl] = []
                    # Simple dedupe by name for the batch
                    if not any(n['name'] == node['name'] for n in entities_by_label[lbl]):
                        entities_by_label[lbl].append(node)
                
                for label, nodes in entities_by_label.items():
                    self.graph_repo.batch_create_nodes(label, nodes)
                    
                # 3. Relationships
                self.graph_repo.batch_create_relationships(relationships)
                
                for doc_id in ids:
                    results_map[doc_id]["steps"]["graph"] = "success"
            else:
                for doc_id in ids:
                    results_map[doc_id]["errors"].append("Graph DB unavailable")
                    
        except Exception as e:
            logger.error(f"Batch Graph failed: {e}")
            for doc_id in ids:
                results_map[doc_id]["errors"].append(f"Graph: {str(e)}")
            
        return list(results_map.values())

    def close(self):
        """Clean up resources."""
        self.graph_repo.close()

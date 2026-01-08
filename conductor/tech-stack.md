# Technology Stack: Real-Time RAG Brain

## Core Infrastructure
- **Language:** Python 3.10+
- **API Framework:** FastAPI for high-performance, asynchronous endpoints.
- **Message Broker:** Redpanda (Kafka-compatible) for real-time event streaming.

## Processing and NLP
- **Distributed Processing:** Apache Spark (PySpark) for transformation and entity extraction from streams.
- **NLP Engine:** spaCy and Hugging Face Transformers for NER (Named Entity Recognition) and relationship extraction.
- **RAG Orchestration:** LangChain and LlamaIndex for managing LLM interactions and memory retrieval patterns.

## Storage Layer
- **Vector Database:** Qdrant for high-performance similarity search and sparse/dense embedding storage.
- **Knowledge Graph:** Neo4j for managing complex relationships, hierarchies, and graph-based reasoning.
- **Cache:** (Inferred) Redis or local memory for transient task states.

## Development and DevOps
- **Containerization:** Docker and Docker Compose for local infrastructure orchestration.
- **Testing:** Pytest for unit and integration testing.
- **LLM Provider:** Ollama (local) for privacy-conscious, low-latency inference.

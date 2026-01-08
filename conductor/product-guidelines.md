# Product Guidelines: Real-Time RAG Brain

## Documentation Strategy
- **Tone and Style:** Formal and Precise. Documentation should prioritize technical accuracy and provide detailed specifications for API contracts, data schemas, and pipeline architectures.
- **Audience:** Primarily developers, data engineers, and AI researchers.

## Design Principles
- **Efficiency First:** Every component in the ingestion and processing pipeline must be optimized for high throughput and low latency.
- **Scalability by Default:** Architectural choices should favor horizontal scaling (e.g., Kafka partitioning, Spark clustering, Neo4j clusters).
- **Hybrid Synergy:** The relationship between vector and graph indices must be treated as a unified memory substrate rather than isolated silos.

## Error Handling and Logging
- **Observability:** Logs must provide high granularity, especially during the extraction and transformation phases, to allow for tracing entity mapping issues.
- **Resilience:** Use robust error handling in the streaming pipeline to ensure that transient failures in database connections do not cause data loss.

## Development Standards
- **Contract-First API:** Define FastAPI models and schemas before implementation to ensure consistency across the stack.
- **Test-Driven Memory:** Implement integration tests that verify both vector retrieval and graph relationship integrity.

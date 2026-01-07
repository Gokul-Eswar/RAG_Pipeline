# Spec: Implement a Smoke Test Suite for the Core Pipeline

## Goal
Establish a basic end-to-end smoke test suite to verify the connectivity and basic functionality of the core Real-Time RAG Brain infrastructure.

## Scope
- Verify FastAPI service health.
- Verify connectivity to Neo4j (Graph Memory).
- Verify connectivity to Qdrant (Vector Memory).
- Implement a basic ingestion-to-retrieval flow check.

## Success Criteria
- All tests pass in the local development environment.
- Tests provide clear error messages for connection failures.

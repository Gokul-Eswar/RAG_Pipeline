# Plan: Consolidate API and Verify Hybrid Retrieval

## Phase 1: API Consolidation [checkpoint: c3a64e2]
- [x] Task: Analyze current API usage in `api/` and `src/api/` to identify overlap and conflicts. dfc9333
- [x] Task: Migrate unique logic from `api/` to `src/api/` following the established `src/` structure. dfc9333
- [x] Task: Update project configuration and run scripts (e.g., `run.py`, `Dockerfile`) to point to `src/api/main:app`. dfc9333
- [x] Task: Remove the redundant `api/` directory. dfc9333
- [x] Task: Conductor - User Manual Verification 'API Consolidation' (Protocol in workflow.md) c3a64e2

## Phase 2: Hybrid Retrieval Integration Testing
- [x] Task: Write TDD integration tests for the unified API retrieval endpoints. bd4e8a7
- [~] Task: Implement a 'Hybrid Health Check' endpoint that verifies connectivity to both Qdrant and Neo4j.
- [ ] Task: Implement the core hybrid retrieval logic (if not already fully functional) ensuring it queries both databases.
- [ ] Task: Verify >80% coverage for the new integration test suite.
- [ ] Task: Conductor - User Manual Verification 'Hybrid Retrieval' (Protocol in workflow.md)

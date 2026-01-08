# Spec: Consolidate API and Verify Hybrid Retrieval

## Overview
The project currently has two API directories: `api/` and `src/api/`. This causes confusion and potential bugs. Additionally, while the system uses both Qdrant (Vector) and Neo4j (Graph), there is no unified integration test to verify that data is correctly synchronized and retrievable via hybrid queries.

## Goals
- Merge `api/` and `src/api/` into a single, clean `src/api/` structure.
- Update all imports and references to the new API path.
- Implement a comprehensive integration test that:
    1. Ingests a sample document.
    2. Verifies it exists in Qdrant (Vector).
    3. Verifies it exists in Neo4j (Graph) with correct relationships.
    4. Performs a hybrid query via the API and confirms the result combines both sources.

## Requirements
- No breaking changes to existing core logic (just pathing and organization).
- 100% pass rate on the new integration test.
- Maintain consistency with `product-guidelines.md` regarding documentation and error handling.

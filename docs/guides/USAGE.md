# Usage Guide

This guide explains how to interact with the Big Data RAG system, focusing on data ingestion, memory management, and retrieval augmented generation (RAG).

## Overview

The system exposes a REST API for all operations. You can interact with it using `curl`, Postman, or any HTTP client.

**Base URL**: `http://localhost:8000`
**Interactive Docs**: `http://localhost:8000/docs`

---

## 1. Authentication

Most endpoints require authentication.
*(Note: Default setup might be open or use basic auth depending on `src/api/security.py`. Check `docs` for current auth method.)*

---

## 2. Ingesting Data

Data enters the system through the ingestion endpoint. This publishes events to the streaming platform (Redpanda/Kafka), which are then processed by the pipeline.

**Endpoint**: `POST /ingest/`

```json
{
  "id": "evt_12345",
  "text": "The quick brown fox jumps over the lazy dog.",
  "metadata": {
    "source": "user_input",
    "timestamp": "2023-10-27T10:00:00Z"
  }
}
```

**Response**:
```json
{
  "status": "received",
  "event_id": "evt_12345"
}
```

---

## 3. Managing Memory (Direct)

While the pipeline automatically processes ingested events into memory, you can also directly manipulate the vector and graph stores.

### Vector Memory (Semantic Search)

**Upsert Vectors**: `POST /memory/upsert`

```json
{
  "collection": "documents",
  "vectors": [
    {
      "id": 1,
      "vector": [0.1, 0.5, ...],  // Optional if using pipeline
      "payload": {
        "text": "Important document content...",
        "category": "finance"
      }
    }
  ]
}
```

**Search Vectors**: `POST /memory/search`

```json
{
  "vector": [0.1, 0.5, ...],
  "limit": 5,
  "collection": "documents"
}
```

### Graph Memory (Relationships)

**Create Node**: `POST /graph/node`

```json
{
  "label": "Person",
  "properties": {
    "name": "Alice",
    "role": "Engineer"
  }
}
```

**Create Relationship**: `POST /graph/relationship`

```json
{
  "from_node": {"label": "Person", "name": "Alice"},
  "to_node": {"label": "Project", "name": "RAG"},
  "type": "WORKS_ON",
  "properties": {"since": 2023}
}
```

---

## 4. Hybrid Search & RAG

This is the core "Brain" functionality, combining vector similarity with graph relationships to generate answers.

### Hybrid Search

Retrieves context using both semantic similarity (Vector DB) and structural relationships (Graph DB).

**Endpoint**: `POST /memory/search/hybrid`

```json
{
  "query_text": "Who is working on the RAG project?",
  "limit": 5
}
```

**Response**:
```json
{
  "status": "ok",
  "results": {
    "semantic": [...],   // Results from Qdrant
    "structural": [...]  // Results from Neo4j
  }
}
```

### RAG Generation (Ask the Brain)

Uses the hybrid context to generate a natural language answer using an LLM (Ollama).

**Endpoint**: `POST /memory/search/generate`

```json
{
  "query_text": "Explain the architecture of the RAG system based on the documents.",
  "limit": 3,
  "model_name": "llama3",
  "include_sources": true
}
```

**Response**:
```json
{
  "status": "ok",
  "answer": "The RAG system architecture consists of...",
  "meta": {
    "model": "llama3",
    "processing_time_ms": 1250
  },
  "sources": { ... }
}
```

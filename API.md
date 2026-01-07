# API Reference

## Overview

The Big Data RAG API provides three main services:

1. **Ingestion** - Publish events to Kafka/Redpanda
2. **Memory (Vector)** - Semantic search with Qdrant
3. **Memory (Graph)** - Entity relationships with Neo4j

All endpoints return JSON responses and support standard HTTP status codes.

---

## System Endpoints

### Health Check
```http
GET /health
```
Verifies the API is running.

**Response (200):**
```json
{
  "status": "ok",
  "service": "Big Data RAG API"
}
```

### Root
```http
GET /
```
Returns API information and links to documentation.

**Response (200):**
```json
{
  "message": "Big Data RAG API",
  "description": "Real-time RAG Brain with streaming data, knowledge graphs, and vector databases",
  "version": "0.1.0",
  "documentation": "/docs"
}
```

---

## Ingestion Endpoints

### Health Check
```http
GET /ingest/health
```
Check Kafka/Redpanda connectivity.

**Response (200):**
```json
{
  "kafka": "redpanda:9092",
  "status": "configured"
}
```

### Publish Event
```http
POST /ingest/
```
Publish a single event to the streaming platform.

**Request Body:**
```json
{
  "id": "event_uuid_123",
  "text": "Raw event content or text data",
  "metadata": {
    "source": "api",
    "timestamp": "2024-01-07T12:00:00Z",
    "user_id": "user_123"
  }
}
```

**Required Fields:**
- `id` (string): Unique event identifier
- `text` (string): Event content (non-empty)

**Optional Fields:**
- `metadata` (object): Additional context

**Response (200):**
```json
{
  "status": "accepted",
  "id": "event_uuid_123",
  "topic": "raw_events",
  "partition": 0,
  "offset": 1234
}
```

**Error Responses:**
- `400 Bad Request`: Missing required field or empty text
- `503 Service Unavailable`: Kafka connection failed
- `500 Internal Server Error`: Processing error

---

## Memory (Vector) Endpoints

### Health Check
```http
GET /memory/health
```
Check Qdrant connectivity.

**Response (200):**
```json
{
  "qdrant": "qdrant:6333",
  "status": "connected"
}
```

### Upsert Vectors
```http
POST /memory/upsert
```
Insert or update vectors in the vector database.

**Request Body:**
```json
{
  "collection": "documents",
  "vectors": [
    {
      "id": 1,
      "vector": [0.1, 0.2, 0.3, ...],
      "payload": {
        "text": "Document content",
        "metadata": {
          "source": "api",
          "document_id": "doc_123"
        }
      }
    }
  ]
}
```

**Fields:**
- `collection` (string, optional): Target collection name (default from env)
- `vectors` (array): List of vectors to upsert
  - `id` (integer): Vector identifier
  - `vector` (array): Embedding vector (typically 384-1536 dimensions)
  - `payload` (object): Associated metadata

**Response (200):**
```json
{
  "status": "ok",
  "collection": "documents",
  "data": {
    "status": "ok",
    "count": 1
  }
}
```

**Error Responses:**
- `400 Bad Request`: Empty vectors array
- `500 Internal Server Error`: Storage or connection error

### Search Vectors
```http
POST /memory/search
```
Find similar vectors using semantic search.

**Request Body:**
```json
{
  "collection": "documents",
  "query_vector": [0.1, 0.2, 0.3, ...],
  "limit": 10
}
```

**Fields:**
- `collection` (string, optional): Collection to search
- `query_vector` (array): Query embedding
- `limit` (integer, default=10): Max results to return

**Response (200):**
```json
{
  "status": "ok",
  "collection": "documents",
  "results": [
    {
      "id": 1,
      "score": 0.95,
      "payload": {
        "text": "Similar document"
      }
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request`: Missing query_vector
- `500 Internal Server Error`: Search failed

### Collection Info
```http
POST /memory/collection/info
```
Get metadata about a collection.

**Request Body:**
```json
{
  "collection": "documents"
}
```

**Response (200):**
```json
{
  "status": "ok",
  "data": {
    "name": "documents",
    "points_count": 1500,
    "vectors_count": 1500,
    "config": "..."
  }
}
```

---

## Graph Endpoints

### Health Check
```http
GET /graph/health
```
Check Neo4j connectivity.

**Response (200):**
```json
{
  "neo4j": "neo4j",
  "status": "connected"
}
```

### Create Node
```http
POST /graph/node
```
Create a node in the graph database.

**Request Body:**
```json
{
  "label": "Document",
  "properties": {
    "title": "Example Document",
    "url": "https://example.com",
    "created_at": "2024-01-07T12:00:00Z"
  }
}
```

**Fields:**
- `label` (string): Node type/label
- `properties` (object): Node attributes

**Response (200):**
```json
{
  "status": "created",
  "data": {
    "node_id": 123,
    "properties": {
      "title": "Example Document",
      "url": "https://example.com",
      "created_at": "2024-01-07T12:00:00Z"
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing or empty label
- `500 Internal Server Error`: Creation failed

### Create Relationship
```http
POST /graph/relationship
```
Create a relationship between two nodes.

**Request Body:**
```json
{
  "from_id": 123,
  "relationship_type": "REFERENCES",
  "to_id": 456,
  "properties": {
    "weight": 0.8,
    "context": "semantic similarity"
  }
}
```

**Fields:**
- `from_id` (integer): Source node ID
- `relationship_type` (string): Relationship type
- `to_id` (integer): Target node ID
- `properties` (object, optional): Relationship attributes

**Response (200):**
```json
{
  "status": "created",
  "data": {
    "relationship_id": 789,
    "type": "REFERENCES"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields
- `500 Internal Server Error`: Creation failed

### Find Node
```http
POST /graph/node/find
```
Find a node by label and properties.

**Request Body:**
```json
{
  "label": "Document",
  "properties": {
    "title": "Example Document"
  }
}
```

**Response (200):**
```json
{
  "status": "found",
  "data": {
    "node_id": 123,
    "properties": {
      "title": "Example Document",
      "url": "https://example.com"
    }
  }
}
```

**Error Responses:**
- `404 Not Found`: No matching node
- `500 Internal Server Error`: Query failed

### Delete Node
```http
DELETE /graph/node/{node_id}
```
Delete a node from the graph.

**Path Parameters:**
- `node_id` (integer): ID of node to delete

**Response (200):**
```json
{
  "status": "deleted",
  "node_id": 123
}
```

**Error Responses:**
- `404 Not Found`: Node doesn't exist
- `500 Internal Server Error`: Deletion failed

---

## Error Handling

All endpoints follow standard HTTP conventions:

- `200 OK` - Request successful
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Backend service unreachable

Error responses include a `detail` field:
```json
{
  "detail": "Detailed error message"
}
```

---

## Authentication

Currently, the API does not require authentication. For production deployment, consider adding:
- API key authentication
- OAuth2
- JWT tokens

---

## Rate Limiting

No rate limiting is currently implemented. For production, consider adding:
- Request rate limits
- Per-endpoint quotas
- Burst protection

---

## Examples

### Example 1: Ingest and Search Workflow

```bash
# 1. Publish event
curl -X POST "http://localhost:8000/ingest/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "doc_1",
    "text": "Machine learning is a subset of artificial intelligence",
    "metadata": {"source": "docs"}
  }'

# 2. Create vector representation (separately)
# Assume you've generated embedding: [0.1, 0.2, ...]

# 3. Upsert vector
curl -X POST "http://localhost:8000/memory/upsert" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "documents",
    "vectors": [
      {
        "id": 1,
        "vector": [0.1, 0.2, 0.3],
        "payload": {"text": "Machine learning is a subset of artificial intelligence"}
      }
    ]
  }'

# 4. Search for similar content
curl -X POST "http://localhost:8000/memory/search" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "documents",
    "query_vector": [0.1, 0.2, 0.3],
    "limit": 5
  }'
```

### Example 2: Graph Operations

```bash
# 1. Create document node
curl -X POST "http://localhost:8000/graph/node" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Document",
    "properties": {"title": "ML Basics", "id": "doc_1"}
  }'

# 2. Create entity node
curl -X POST "http://localhost:8000/graph/node" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Concept",
    "properties": {"name": "Machine Learning"}
  }'

# 3. Create relationship (use node IDs from above responses)
curl -X POST "http://localhost:8000/graph/relationship" \
  -H "Content-Type: application/json" \
  -d '{
    "from_id": 1,
    "relationship_type": "MENTIONS",
    "to_id": 2,
    "properties": {"confidence": 0.95}
  }'
```

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API exploration and request/response examples.

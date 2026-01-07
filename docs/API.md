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

## Vector Memory Endpoints

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
- `collection` (string, optional): Target collection name
- `vectors` (array): List of vectors to upsert

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

---

## Graph Memory Endpoints

### Health Check
```http
GET /graph/health
```
Check Neo4j connectivity.

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
    "url": "https://example.com"
  }
}
```

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
    "weight": 0.8
  }
}
```

### Find Node
```http
POST /graph/node/find
```
Find a node by label and properties.

### Delete Node
```http
DELETE /graph/node/{node_id}
```
Delete a node from the graph.

---

## Error Handling

Standard HTTP conventions:
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service unavailable

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

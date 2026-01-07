# Architecture Overview

## System Design

The Big Data RAG system follows a **Clean Architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                      API Layer                          │
│  (FastAPI - HTTP handlers)                              │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│              Infrastructure Layer                       │
│  ├─ Database: Neo4j, Qdrant                             │
│  └─ Messaging: Kafka/Redpanda                           │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│            Business Logic / Processing                  │
│  ├─ Ingestion: Event streaming                          │
│  ├─ Extraction: NLP pipelines                           │
│  └─ Transformation: Data processing                     │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/
├── api/                    # API Layer
│   ├── handlers/          # HTTP route handlers
│   │   ├── events.py      # Event ingestion
│   │   ├── vectors.py     # Vector search
│   │   └── graphs.py      # Graph operations
│   ├── middleware/        # Error handling, auth
│   └── main.py            # FastAPI app factory
│
├── infrastructure/        # External Services
│   ├── database/
│   │   ├── neo4j.py       # Graph database client
│   │   └── qdrant.py      # Vector database client
│   └── messaging/
│       └── kafka.py       # Event producer
│
├── processing/           # Business Logic
│   ├── ingestion/
│   │   └── producer.py    # Event publication
│   ├── extraction/
│   │   └── nlp.py        # NLP processing
│   └── transformation/
│       └── spark.py      # Distributed processing
│
├── storage/              # Storage Abstraction
│   ├── vector/
│   │   └── repository.py  # Vector operations
│   └── graph/
│       └── repository.py  # Graph operations
│
├── ai/                   # LLM Integration
│   └── models/
│       └── language_models.py
│
├── orchestration/        # Workflow Management
│   └── airflow/
│       └── dags.py
│
├── models/              # Domain Models
│   └── domain.py        # Data models
│
├── utils/              # Utilities
│   ├── config.py       # Configuration
│   └── logging.py      # Logging setup
│
└── core/               # Core Application
    └── cli.py          # CLI interface
```

## Data Flow

### Event Ingestion Flow

```
External Event
       │
       ▼
POST /ingest/
       │
       ▼
KafkaEventProducer ──────► Redpanda Topic
       │
       ▼
Confirmation Response
```

### Vector Memory Flow

```
Raw Text
       │
       ▼
Generate Embeddings
       │
       ▼
POST /memory/upsert
       │
       ▼
QdrantVectorRepository ──► Qdrant Collection
       │
       ▼
POST /memory/search
       │
       ▼
Similar Results
```

### Graph Memory Flow

```
Extracted Entities
       │
       ▼
POST /graph/node
       │
       ▼
Neo4jGraphRepository ──► Neo4j Database
       │
       ▼
Node Created
       │
       ▼
POST /graph/relationship
       │
       ▼
Neo4jGraphRepository ──► Neo4j Database
       │
       ▼
Relationship Created
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API | FastAPI | HTTP server |
| Ingestion | Kafka/Redpanda | Event streaming |
| Processing | Spark | Distributed computing |
| Extraction | spaCy/Transformers | NLP |
| Vector Memory | Qdrant | Semantic search |
| Graph Memory | Neo4j | Knowledge graphs |
| Orchestration | Airflow | Workflow management |
| LLM | Ollama | Local inference |
| Database | PostgreSQL | Metadata store |

## Design Patterns

### Repository Pattern
All database access goes through repository classes:
- `Neo4jGraphRepository` - Graph operations
- `QdrantVectorRepository` - Vector operations

### Handler Pattern
HTTP requests are handled by handler functions:
- `events.py` - Ingestion handlers
- `vectors.py` - Memory (vector) handlers
- `graphs.py` - Memory (graph) handlers

### Producer Pattern
Events are published through producer classes:
- `KafkaEventProducer` - Kafka publishing

## Deployment Architecture

### Development
- Single machine with Docker Compose
- All services in containers
- Shared network

### Production (Planned)
- Kubernetes orchestration
- Separate database nodes
- Load-balanced API servers
- Message queue cluster
- Monitoring and logging

## Security Considerations

- [ ] API Authentication (JWT tokens)
- [ ] Database credentials in secrets manager
- [ ] TLS for all connections
- [ ] Rate limiting per endpoint
- [ ] Input validation on all endpoints
- [ ] Audit logging

## Performance Considerations

- Qdrant indexes for fast vector search
- Neo4j query optimization
- Kafka partitioning for scalability
- Connection pooling for databases
- Caching layer (future)
- Async processing (future)

# Setup Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- 8GB RAM minimum
- 10GB disk space

## Local Development Setup

### 1. Clone and Environment

```bash
# Navigate to project
cd Big_Data_RAG

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings (optional, defaults work for local dev)
```

### 3. Start Backend Services

```bash
# Navigate to docker directory
cd docker

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Run Application

```bash
# Option A: Run API server
python -m uvicorn src.api.main:app --reload --port 8000

# Option B: Run CLI
python run.py

# Option C: Run tests
pytest
```

### 5. Access Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Airflow | http://localhost:8080 |
| Neo4j Browser | http://localhost:7474 |
| Qdrant UI | http://localhost:6333/dashboard |

---

## Docker Setup Details

### Services

The `docker-compose.yml` includes:

- **Redpanda**: Kafka-compatible message broker
- **Qdrant**: Vector database
- **Neo4j**: Graph database
- **PostgreSQL**: Metadata store
- **Airflow**: Workflow orchestration
- **Spark**: Distributed processing

### Common Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Access service shell
docker-compose exec [service_name] /bin/bash

# Restart service
docker-compose restart [service_name]

# Rebuild images
docker-compose build --no-cache

# Clean everything
docker-compose down -v
```

### Service Access

**Neo4j**
- Browser: http://localhost:7474
- Username: neo4j
- Password: test

**Airflow**
- Web UI: http://localhost:8080
- Username: admin
- Password: admin

---

## Development Workflow

### Running Tests

```bash
# All tests
pytest

# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# With coverage
pytest --cov=src --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/
```

### Code Quality

```bash
# Format
black src/ tests/

# Type check
mypy src/

# Lint
flake8 src/ tests/

# All at once
black . && mypy src/ && flake8 . && pytest
```

### Making API Requests

```bash
# Ingest event
curl -X POST http://localhost:8000/ingest/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "event_1",
    "text": "Sample text",
    "metadata": {"source": "test"}
  }'

# Upsert vector
curl -X POST http://localhost:8000/memory/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "docs",
    "vectors": [{
      "id": 1,
      "vector": [0.1, 0.2, ...],
      "payload": {"text": "sample"}
    }]
  }'

# Create graph node
curl -X POST http://localhost:8000/graph/node \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Document",
    "properties": {"title": "Test"}
  }'
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# Kill process
# Linux/Mac
kill -9 <PID>

# Windows
taskkill /PID <PID> /F
```

### Docker Issues

```bash
# Clear all containers
docker-compose down -v

# Rebuild services
docker-compose build --no-cache

# Check Docker daemon
docker info
```

### Kafka/Redpanda Connection

```bash
# Check if service is running
docker-compose ps

# View logs
docker-compose logs redpanda

# Test connection
docker-compose exec redpanda rpk cluster info
```

### Database Connection

```bash
# Test Neo4j
docker-compose exec neo4j cypher-shell -u neo4j -p test

# Test Qdrant
curl http://localhost:6333/health
```

---

## Production Deployment

See deployment guides in `docs/deployment/` (coming soon)

## Getting Help

- Check existing documentation in `docs/`
- Review test files for usage examples
- Open an issue on GitHub

# Setup Guide

## Prerequisites

- **OS**: Linux, macOS, or Windows (WSL2 recommended)
- **Python**: 3.11+
- **Docker**: Docker Desktop or Engine + Compose
- **Ollama**: For local LLM inference (install from [ollama.ai](https://ollama.ai))
- **Hardware**: 8GB RAM minimum (16GB recommended for LLMs)

## 1. Local Development Setup

### Clone and Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/Big_Data_RAG.git
cd Big_Data_RAG

# Create virtual environment
python -m venv .venv

# Activate
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment

Copy the example configuration:
```bash
cp .env.example .env
```

**Key Configuration Variables (.env)**

| Variable | Description | Default (Local) |
|----------|-------------|-----------------|
| `KAFKA_BROKER` | Kafka/Redpanda address | `localhost:9092` |
| `QDRANT_HOST` | Vector DB Host | `localhost` |
| `NEO4J_URI` | Graph DB URI | `bolt://localhost:7687` |
| `NEO4J_PASSWORD` | Graph DB Password | `test` |
| `OLLAMA_HOST` | LLM Service URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM Model Name | `llama3` |

*Note: When running services via Docker, the internal hostnames (e.g., `redpanda`, `neo4j`) are used. When running the API locally on your host machine, you may need to ensure these point to `localhost` or update your `.env` accordingly.*

## 2. Start Infrastructure

Use Docker Compose to spin up the backing services (Database, Message Queue, etc.).

```bash
cd docker
docker-compose up -d
```

**Verify Services:**
- **Neo4j**: http://localhost:7474 (Login: `neo4j` / `test`)
- **Qdrant**: http://localhost:6333/dashboard
- **Redpanda**: http://localhost:8081 (if console enabled)
- **Airflow**: http://localhost:8080 (Login: `admin` / `admin`)

## 3. Run the Application

You can run the API directly on your host machine for easier development.

```bash
# Run the API server
python run.py api
```

The API will be available at `http://localhost:8000`.

## 4. Troubleshooting

### Port Conflicts
If ports 8000, 7474, 6333, or 9092 are in use, you will need to stop the conflicting services or change the port mapping in `docker/docker-compose.yml`.

### Database Connection Issues
If the API cannot connect to Neo4j or Qdrant:
1. Ensure Docker containers are running (`docker ps`).
2. Check `.env` matches the exposed ports (usually `localhost` for local dev).
3. Wait a few seconds for databases to initialize.

### LLM Errors
If Ollama is not reachable:
1. Ensure Ollama is running (`ollama serve`).
2. Pull the required model: `ollama pull llama3`.

## Next Steps

Head over to the **[Usage Guide](USAGE.md)** to start ingesting data and asking questions.
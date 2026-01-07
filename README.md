# Real-Time RAG Brain

An autonomous intelligence substrate integrating streaming data, knowledge graphs, and vector databases to create a living, updating digital brain.

## Architecture

This project implements a fully open-source stack as described in `context.md`:

| Component | Technology | Directory |
|-----------|------------|-----------|
| **Ingestion** | Redpanda (Kafka) | `/ingestion` |
| **Processing** | Apache Spark | `/processing` |
| **Extraction** | spaCy / Transformers | `/extraction` |
| **Memory (Vector)** | Milvus / Qdrant | `/memory/vector` |
| **Memory (Graph)** | Neo4j | `/memory/graph` |
| **API** | FastAPI | `/api` |
| **Orchestration** | Airflow / Dagster | `/orchestration` |
| **LLM** | Ollama (LLaMA 3 / DeepSeek) | `/llm` |

## Setup

1.  **Infrastructure**: Use Docker Compose to spin up the required services.
    ```bash
    cd docker
    docker-compose up -d
    ```

2.  **Dependencies**: Install Python requirements.
    ```bash
    pip install -r requirements.txt
    ```

## Workflow

`Live world → events → entities → relations → vectors → graph → memory → AI`

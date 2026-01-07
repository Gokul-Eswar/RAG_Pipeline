# Real-Time RAG Brain

An autonomous intelligence substrate integrating streaming data, knowledge graphs, and vector databases to create a living, updating digital brain.

## Architecture

This project implements a fully open-source stack:

| Component | Technology |
|-----------|------------|
| **Ingestion** | Redpanda (Kafka) |
| **Processing** | Apache Spark |
| **Extraction** | spaCy / Transformers |
| **Memory (Vector)** | Milvus / Qdrant |
| **Memory (Graph)** | Neo4j |
| **API** | FastAPI |
| **Orchestration** | Airflow / Dagster |
| **LLM** | Ollama (LLaMA 3 / DeepSeek) |

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

"""Core CLI interface."""

from src.utils.config import Config


def main():
    """Application entry point."""
    print("Big Data RAG System — initialized")
    print(f"API: {Config.API_HOST}:{Config.API_PORT}")
    print(f"Kafka: {Config.KAFKA_BROKER}")
    print(f"Neo4j: {Config.NEO4J_URI}")
    print(f"Qdrant: {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")


if __name__ == "__main__":
    main()

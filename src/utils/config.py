"""Utility functions and configuration."""

import os
from typing import Optional


class Config:
    """Application configuration."""
    
    DEBUG = os.getenv("DEBUG", "False") == "True"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Kafka
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda:9092")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_INGESTION", "raw_events")
    
    # Qdrant
    QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_DEFAULT", "documents")
    
    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_AUTH = os.getenv("NEO4J_AUTH", "neo4j/test")
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Spark
    SPARK_MASTER = os.getenv("SPARK_MASTER", "spark://spark:7077")
    SPARK_APP_NAME = os.getenv("SPARK_APP_NAME", "BigDataRAG-Transformer")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-default-key-for-dev-only")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost,http://localhost:3000").split(",")

    # Resilience
    RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    RETRY_MIN_WAIT = float(os.getenv("RETRY_MIN_WAIT", "1.0"))
    RETRY_MAX_WAIT = float(os.getenv("RETRY_MAX_WAIT", "10.0"))
    
    # Timeouts (seconds)
    NEO4J_TIMEOUT = int(os.getenv("NEO4J_TIMEOUT", "5"))
    QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", "10"))
    KAFKA_TIMEOUT = int(os.getenv("KAFKA_TIMEOUT", "3"))

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> str:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        return getattr(cls, key, default)

    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.DEBUG and cls.SECRET_KEY == "unsafe-default-key-for-dev-only":
            raise ValueError("SECRET_KEY must be set in production environment")
        
        if not cls.NEO4J_AUTH:
            raise ValueError("NEO4J_AUTH environment variable is required")

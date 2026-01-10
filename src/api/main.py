"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.handlers import auth_router, events_router, vectors_router, graphs_router, hybrid_router
from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository
from src.utils.config import Config


from src.api.middleware.error_handlers import (
    validation_exception_handler,
    app_exception_handler,
    circuit_breaker_handler,
    global_exception_handler
)
from src.utils.exceptions import AppError
from circuitbreaker import CircuitBreakerError
from fastapi.exceptions import RequestValidationError


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="Big Data RAG API",
        description="Real-time RAG Brain - Ingestion, Vector Memory, and Graph Database Integration",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Initialize Rate Limiter
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # Exception Handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AppError, app_exception_handler)
    app.add_exception_handler(CircuitBreakerError, circuit_breaker_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["System"])
    def health_check():
        """Health check - verifies API is running."""
        return {"status": "ok", "service": "Big Data RAG API"}

    @app.get("/health/hybrid", tags=["System"])
    def hybrid_health_check():
        """Hybrid health check - verifies connectivity to both Qdrant and Neo4j."""
        neo4j_repo = Neo4jGraphRepository()
        qdrant_repo = QdrantVectorRepository()
        
        neo4j_status = neo4j_repo.check_connectivity()
        qdrant_status = qdrant_repo.check_connectivity()
        
        neo4j_repo.close()
        
        status = "ok" if neo4j_status and qdrant_status else "degraded"
        
        return {
            "status": status,
            "components": {
                "neo4j": "connected" if neo4j_status else "disconnected",
                "qdrant": "connected" if qdrant_status else "disconnected"
            }
        }

    @app.get("/", tags=["System"])
    def root_endpoint():
        """Root endpoint - returns API information."""
        return {
            "message": "Big Data RAG API",
            "description": "Real-time RAG Brain with streaming data, knowledge graphs, and vector databases",
            "version": "0.1.0",
            "documentation": "/docs"
        }

    # Include routers
    app.include_router(auth_router)
    app.include_router(events_router)
    app.include_router(vectors_router)
    app.include_router(graphs_router)
    app.include_router(hybrid_router)

    # Configure OpenAPI
    app.openapi = lambda: _custom_openapi(app)
    
    return app


def _custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Big Data RAG API",
        version="0.1.0",
        description="""
        A real-time RAG (Retrieval Augmented Generation) system that integrates:
        
        - **Ingestion**: Event streaming via Kafka/Redpanda
        - **Memory (Vector)**: Semantic search with Qdrant
        - **Memory (Graph)**: Entity relationships with Neo4j
        - **Processing**: Apache Spark for data transformation
        - **LLM**: Local inference with Ollama
        
        ## Workflow
        
        `Events → Extraction → Vectors → Graph → Memory → AI`
        
        ## Core Endpoints
        
        ### Event Ingestion
        - `POST /ingest/` - Publish events to streaming platform
        
        ### Vector Memory (Semantic Search)
        - `POST /memory/upsert` - Store vectors with metadata
        - `POST /memory/search` - Find similar vectors
        - `POST /memory/collection/info` - Get collection stats
        
        ### Graph Memory (Entity Relationships)
        - `POST /graph/node` - Create entity nodes
        - `POST /graph/relationship` - Link entities
        - `POST /graph/node/find` - Query entities
        - `DELETE /graph/node/{id}` - Remove entities
        """,
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create the app instance
app = create_app()

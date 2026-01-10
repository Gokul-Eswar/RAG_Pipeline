"""FastAPI application factory."""

import uuid
import time
import json
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.api.handlers import auth_router, events_router, vectors_router, graphs_router, hybrid_router
from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository
from src.utils.config import Config
from src.utils.logging import setup_logging, correlation_id
from src.utils.metrics import REQUEST_COUNT, REQUEST_DURATION

from src.api.middleware.error_handlers import (
    validation_exception_handler,
    app_exception_handler,
    circuit_breaker_handler,
    global_exception_handler
)
from src.utils.exceptions import AppError
from circuitbreaker import CircuitBreakerError
from fastapi.exceptions import RequestValidationError

# Setup logging
setup_logging(Config.LOG_LEVEL)


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

    # Metrics Middleware
    @app.middleware("http")
    async def track_metrics(request: Request, call_next):
        """Track request metrics."""
        start_time = time.time()
        
        # Don't track metrics endpoint itself to avoid noise
        if request.url.path == "/metrics":
            return await call_next(request)
            
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status_code
            ).inc()
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

    # Correlation ID Middleware
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next):
        """Add correlation ID to request context and response headers."""
        request_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        token = correlation_id.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = request_id
            return response
        finally:
            correlation_id.reset(token)

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

    @app.get("/metrics", tags=["System"])
    def metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health/live", tags=["System"])
    def liveness():
        """Kubernetes liveness probe."""
        return {"status": "alive"}

    @app.get("/health/ready", tags=["System"])
    async def readiness():
        """Kubernetes readiness probe."""
        neo4j_repo = Neo4jGraphRepository()
        qdrant_repo = QdrantVectorRepository()
        
        checks = {
            "neo4j": neo4j_repo.check_connectivity(),
            "qdrant": qdrant_repo.check_connectivity(),
            # Kafka check would go here
        }
        
        neo4j_repo.close()
        
        if all(checks.values()):
            return {"status": "ready", "checks": checks}
        else:
            return Response(
                content=json.dumps({"status": "not_ready", "checks": checks}),
                status_code=503,
                media_type="application/json"
            )

    @app.get("/health", tags=["System"])
    def health_check():
        """Legacy health check - verifies API is running."""
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

"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from src.api.handlers import events_router, vectors_router, graphs_router


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

    @app.get("/health", tags=["System"])
    def health_check():
        """Health check - verifies API is running."""
        return {"status": "ok", "service": "Big Data RAG API"}

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
    app.include_router(events_router)
    app.include_router(vectors_router)
    app.include_router(graphs_router)

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

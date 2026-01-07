from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from .routers import ingest, memory, graph


app = FastAPI(
    title="Big Data RAG API",
    description="Real-time RAG Brain - Ingestion, Vector Memory, and Graph Database Integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health", tags=["System"])
def health():
    """Health check - verifies API is running."""
    return {"status": "ok", "service": "Big Data RAG API"}


@app.get("/", tags=["System"])
def root():
    """Root endpoint - returns API information."""
    return {
        "message": "Big Data RAG API",
        "description": "Real-time RAG Brain with streaming data, knowledge graphs, and vector databases",
        "version": "0.1.0",
        "documentation": "/docs"
    }


# Include routers with prefixes and documentation
app.include_router(
    ingest.router,
    tags=["Ingestion"],
)
app.include_router(
    memory.router,
    tags=["Memory"],
)
app.include_router(
    graph.router,
    tags=["Graph"],
)


def custom_openapi():
    """Custom OpenAPI schema with enhanced documentation."""
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
        
        ## Endpoints
        
        ### Ingestion
        - `POST /ingest/` - Publish events to streaming platform
        
        ### Memory (Vector)
        - `POST /memory/upsert` - Upsert vectors into Qdrant
        - `POST /memory/search` - Search for similar vectors
        - `POST /memory/collection/info` - Get collection metadata
        
        ### Memory (Graph)
        - `POST /graph/node` - Create a node in Neo4j
        - `POST /graph/relationship` - Create a relationship
        - `POST /graph/node/find` - Find a node by properties
        - `DELETE /graph/node/{node_id}` - Delete a node
        """,
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

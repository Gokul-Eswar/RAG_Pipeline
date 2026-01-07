from fastapi import FastAPI
from .routers import ingest, memory, graph


app = FastAPI(title="Big Data RAG API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Big Data RAG API — replace with real endpoints"}


app.include_router(ingest.router)
app.include_router(memory.router)
app.include_router(graph.router)

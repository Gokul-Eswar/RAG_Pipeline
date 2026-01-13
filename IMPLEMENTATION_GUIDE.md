# Implementation Guide - Final Polish (2-3 Weeks)

**Start Date**: January 13, 2026  
**Target Completion**: January 27-30, 2026  
**Team Size**: 1 developer (you!)  
**Current Status**: 75-80% complete, 6 items remaining

---

## COMPLETED ✅

### Security Integration ✅ **DONE**
- ✅ JWT with Redis backend fully integrated
- ✅ Applied to all POST/PUT/DELETE endpoints
- ✅ API Keys supported and configured
- ✅ All 4 handlers protected with `@Depends(get_current_active_user)`

### Resilience Patterns ✅ **DONE**
- ✅ @get_retry_decorator on all DB/Kafka operations (20 matches)
- ✅ @get_circuit_breaker on all external services (19 matches)
- ✅ Named by operation (neo4j_create_node, qdrant_search, kafka_publish)
- ✅ Exception handling catches CircuitBreakerError and returns 503

### Observability ✅ **INFRASTRUCTURE COMPLETE**
- ✅ JSON logging with pythonjsonlogger configured
- ✅ Prometheus metrics at /metrics endpoint
- ✅ Correlation ID middleware tracking
- ✅ Health probes for Kubernetes
- ⚠️ Handlers need to actively use logging (3-4h remaining)

### Performance ✅ **OPTIMIZED**
- ✅ Connection pooling configured for Neo4j and Qdrant
- ✅ @cache_result decorator on queries (11 matches)
- ✅ Caching integrated in repositories
- ✅ Configuration validation in place

---

## Phase 1: Search Endpoint Auth Decision (1-2 hours)
**Priority**: MEDIUM | **Owner**: Dev (you)

### Task 1.1: Review Search Endpoints (30 min)
**Files**: 
- `src/api/handlers/vectors.py` - search_vectors endpoint
- `src/api/handlers/graphs.py` - find_graph_node endpoint
- `src/api/handlers/vectors.py` - collection/info endpoint

Current state: These endpoints are **READ-ONLY** (no authentication):

```python
# vectors.py - Line 45
@router.post("/search")
def search_vectors(request: SearchVectorsRequest):  # ← No Depends() for auth
    """Search for similar vectors (read-only)."""
    
# graphs.py - Line 38
@router.post("/node/find")
def find_graph_node(request: NodeQueryRequest):  # ← No Depends() for auth
    """Find nodes in graph (read-only)."""
```

### Task 1.2: Make Decision (15 min)

**Option A: Keep Public (RECOMMENDED)**
- Read-only operations are safe
- Simplifies API usage
- Follows REST best practices
- ✅ This is fine

**Option B: Add Authentication**
- More restrictive
- Every request requires token
- Better for private use cases

### Task 1.3: Document Decision (15 min)
Create a comment in each file documenting why it's public/private:

```python
# vectors.py - Line 45
# NOTE: Search is intentionally public (read-only, no data modification)
# Authentication required only for data writes (upsert)
@router.post("/search")
def search_vectors(request: SearchVectorsRequest):
    """Search for similar vectors (PUBLIC endpoint)."""
```

### Task 1.3: Update Vectors Handler (3 hours)
**File**: `src/api/handlers/vectors.py`

Apply same pattern to all POST/PUT/DELETE endpoints:
- [ ] `/search` - GET (read-only, can allow without auth OR with read permission)
- [ ] `/upsert` - POST (requires auth)
- [ ] `/delete` - DELETE (requires auth)

### Task 1.4: Update Graphs Handler (3 hours)
**File**: `src/api/handlers/graphs.py`

Apply same pattern to:
- [ ] `/create` - POST (requires auth)
- [ ] `/query` - GET (optional auth OR read permission)
- [ ] `/delete` - DELETE (requires auth)

### Task 1.5: Update Hybrid Handler (2 hours)
**File**: `src/api/handlers/hybrid.py`

Apply same pattern to all sensitive endpoints.

### Task 1.6: Test & Validate (2 hours)
**Files**: `tests/integration/test_api_handlers.py`

Add tests:
```python
def test_ingest_requires_authentication():
    """POST /ingest/ should reject requests without auth."""
    response = client.post("/ingest/", json={...})
    assert response.status_code == 401

def test_ingest_accepts_valid_token():
    """POST /ingest/ should accept valid JWT token."""
    token = create_test_token(user="test_user")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/ingest/", headers=headers, json={...})
    assert response.status_code == 200
```

**Validation Steps**:
- [ ] Run pytest: `pytest tests/integration/test_api_handlers.py -v`
- [ ] Test with `curl` using token
- [ ] Verify 401 responses for missing auth
- [ ] Check OpenAPI docs show auth requirement

---

## Phase 2: Resilience Integration (Weeks 1-2)
**Timeline**: 2-3 days | **Priority**: CRITICAL | **Owner**: Dev 1

### Task 2.1: Review Resilience Decorators (2 hours)
**File**: `src/utils/resilience.py`

Current implementation:
- ✅ `get_retry_decorator()` with exponential backoff
- ✅ `get_circuit_breaker()` with threshold/timeout
- ✅ Proper logging on retry

### Task 2.2: Integrate Retry/Circuit Breaker into Events (4 hours)
**File**: `src/api/handlers/events.py`

```python
# Current (NO RESILIENCE)
from src.infrastructure.messaging.kafka import KafkaEventProducer

@router.post("/")
def ingest_event(request: IngestEventRequest, current_user: User = Depends(...)):
    producer = KafkaEventProducer()
    result = producer.publish(message)  # ❌ Fails completely on error

# FIXED (WITH RESILIENCE)
from src.utils.resilience import get_retry_decorator, get_circuit_breaker

@router.post("/")
@get_retry_decorator(
    max_attempts=3,
    min_wait=1.0,
    max_wait=10.0,
    exceptions=(KafkaError, TimeoutError)
)
@get_circuit_breaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="kafka_ingest"
)
def publish_to_kafka(message: dict):
    """Publish with automatic retry and circuit breaker."""
    producer = KafkaEventProducer()
    return producer.publish(message)

@router.post("/")
def ingest_event(request: IngestEventRequest, current_user: User = Depends(...)):
    try:
        result = publish_to_kafka({...})
        return {"status": "accepted", "id": request.id}
    except CircuitBreakerError:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
```

**Checklist**:
- [ ] Import `get_retry_decorator` and `get_circuit_breaker`
- [ ] Add decorators to critical operations
- [ ] Handle `CircuitBreakerError` appropriately
- [ ] Test failure scenarios

### Task 2.3: Integrate Resilience into Vectors Handler (3 hours)
**File**: `src/api/handlers/vectors.py`

Apply resilience to:
- Qdrant upsert operations
- Qdrant search operations
- Neo4j relationship queries

```python
@get_retry_decorator(exceptions=(SearchError, TimeoutError))
@get_circuit_breaker(name="qdrant_search")
def search_vectors(query_embedding, limit):
    return qdrant_client.search(...)
```

### Task 2.4: Integrate Resilience into Graphs Handler (3 hours)
**File**: `src/api/handlers/graphs.py`

Apply resilience to:
- Neo4j node creation
- Neo4j relationship creation
- Neo4j query operations

```python
@get_retry_decorator(exceptions=(ServiceUnavailable, TransientError))
@get_circuit_breaker(name="neo4j_operations")
def create_node(label, properties):
    return neo4j_repo.create_node(label, properties)
```

### Task 2.5: Test Resilience (3 hours)
**File**: `tests/unit/test_resilience.py` (already exists, extend it)

Add tests:
```python
def test_event_ingest_retries_on_kafka_error():
    """Ingest should retry on KafkaError."""
    with patch('kafka.KafkaProducer.send', side_effect=KafkaError()):
        # Should retry 3 times
        with pytest.raises(KafkaError):
            ingest_event(...)

def test_circuit_breaker_opens_on_repeated_failures():
    """Circuit breaker should open after 5 failures."""
    # Simulate 5 failures
    # Assert 6th call raises CircuitBreakerError immediately
```

**Validation**:
- [ ] Run: `pytest tests/unit/test_resilience.py -v`
- [ ] Manually test with killed database (should get graceful response)
- [ ] Verify metrics show retry counts

---

## Phase 3: Observability (Weeks 2-3)
**Timeline**: 3-4 days | **Priority**: HIGH | **Owner**: Dev 2

### Task 3.1: Implement Structured JSON Logging (2 hours)
**File**: `src/utils/logging.py` (UPDATE)

```python
# Current logging setup - NEEDS JSON IMPROVEMENT
import logging

# IMPROVED - Add JSON structured logging
import logging
from pythonjsonlogger import jsonlogger

def setup_logging(log_level="INFO"):
    """Setup JSON structured logging."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Console handler with JSON formatter
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s %(request_id)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Usage in handlers
logger = logging.getLogger(__name__)
logger.info("Event processed", extra={
    "event_id": request.id,
    "user_id": current_user.id,
    "status": "accepted",
    "duration_ms": elapsed_time
})
```

**Changes Needed**:
- [ ] Add `python-json-logger` to requirements.txt
- [ ] Update logging setup to use JSON formatter
- [ ] Add request correlation ID to all logs
- [ ] Remove plain print() statements

### Task 3.2: Add Prometheus Metrics (2 hours)
**File**: `src/api/main.py` (UPDATE) & `src/utils/metrics.py` (UPDATE)

```python
# In main.py - Add metrics endpoint
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# In handlers - Record metrics
from src.utils.metrics import REQUEST_COUNT, REQUEST_DURATION

@router.post("/")
async def ingest_event(...):
    start = time.time()
    try:
        # ... business logic
        REQUEST_COUNT.labels(
            method="POST",
            endpoint="/ingest",
            status=200
        ).inc()
    finally:
        duration = time.time() - start
        REQUEST_DURATION.labels(
            method="POST",
            endpoint="/ingest"
        ).observe(duration)
```

**Checklist**:
- [ ] Add `/metrics` endpoint
- [ ] Create metrics for all key operations
- [ ] Record latency for database operations
- [ ] Count errors by type

### Task 3.3: Integrate Correlation IDs (2 hours)
**File**: `src/utils/logging.py` & `src/api/main.py` (already has middleware)

Make sure correlation IDs are in:
- [ ] All log output
- [ ] Response headers (X-Correlation-ID)
- [ ] Database operations for tracing

```python
# Use in logging
logger.info("Query executed", extra={
    "correlation_id": correlation_id.get(),
    "query": query_string,
    "duration_ms": elapsed
})
```

### Task 3.4: Add Health Check Endpoints (2 hours)
**File**: `src/api/handlers/health.py` (CREATE NEW)

```python
"""Health check endpoints for Kubernetes."""

from fastapi import APIRouter, HTTPException
from src.infrastructure.database.neo4j import Neo4jGraphRepository
from src.infrastructure.database.qdrant import QdrantVectorRepository

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/live", description="Liveness probe")
async def liveness():
    """Service is running."""
    return {"status": "alive"}

@router.get("/ready", description="Readiness probe")
async def readiness():
    """Service is ready to handle requests."""
    try:
        # Check dependencies
        neo4j_ok = Neo4jGraphRepository().driver is not None
        qdrant_ok = QdrantVectorRepository().client is not None
        
        if neo4j_ok and qdrant_ok:
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Dependencies unavailable")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")
```

Add to main.py:
```python
from src.api.handlers.health import router as health_router
app.include_router(health_router)
```

### Task 3.5: Validate Observability (2 hours)

**Checklist**:
- [ ] Run application and check `/metrics` endpoint
- [ ] Verify JSON logs format: `docker logs <container> | jq .`
- [ ] Check correlation IDs in logs
- [ ] Test health endpoints: `curl http://localhost:8000/health/live`
- [ ] Verify Prometheus can scrape metrics

---

## Phase 4: Performance Optimization (Weeks 3-4)
**Timeline**: 3-4 days | **Priority**: HIGH | **Owner**: Dev 2

### Task 4.1: Optimize Neo4j Connection Pooling (2 hours)
**File**: `src/utils/config.py` (ADD) & `src/infrastructure/database/neo4j.py` (UPDATE)

```python
# In config.py - ADD these
class Config:
    # Neo4j Pooling
    NEO4J_MAX_POOL_SIZE = int(os.getenv("NEO4J_MAX_POOL_SIZE", "50"))
    NEO4J_CONNECTION_TIMEOUT = int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "10"))
    NEO4J_CONNECTION_ACQUISITION_TIMEOUT = int(os.getenv("NEO4J_CONNECTION_ACQUISITION_TIMEOUT", "30"))
    NEO4J_MAX_TRANSACTION_RETRY_TIME = int(os.getenv("NEO4J_MAX_TRANSACTION_RETRY_TIME", "30"))
    
    # Qdrant Pooling
    QDRANT_CONNECTION_POOL_SIZE = int(os.getenv("QDRANT_CONNECTION_POOL_SIZE", "20"))
    QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", "30"))
```

```python
# In neo4j.py - UPDATE driver creation
@staticmethod
def _get_driver():
    """Get or create Neo4j driver with connection pooling."""
    if GraphDatabase is None:
        return None
    
    uri = Config.NEO4J_URI
    auth = Config.NEO4J_AUTH.split("/")
    
    return GraphDatabase.driver(
        uri,
        auth=(auth[0], auth[1] if len(auth) > 1 else ""),
        max_connection_pool_size=Config.NEO4J_MAX_POOL_SIZE,  # ✅ Use config
        connection_acquisition_timeout=Config.NEO4J_CONNECTION_ACQUISITION_TIMEOUT,  # ✅
        connection_timeout=Config.NEO4J_CONNECTION_TIMEOUT  # ✅
    )
```

### Task 4.2: Optimize Qdrant Connection Pooling (2 hours)
**File**: `src/infrastructure/database/qdrant.py` (UPDATE)

```python
# In qdrant.py - Add connection pooling
from qdrant_client import QdrantClient, models

class QdrantVectorRepository:
    _client = None  # Singleton pattern
    
    def __init__(self, collection_name="documents"):
        if QdrantVectorRepository._client is None:
            QdrantVectorRepository._client = QdrantClient(
                host=Config.QDRANT_HOST,
                port=Config.QDRANT_PORT,
                timeout=Config.QDRANT_TIMEOUT,
                prefer_grpc=True  # More efficient than HTTP
            )
        self.client = QdrantVectorRepository._client
        self.collection_name = collection_name
```

### Task 4.3: Implement Result Caching (3 hours)
**File**: `src/api/handlers/vectors.py` (UPDATE)

```python
# Current - NO CACHING
@router.post("/search")
def search_vectors(query: SearchQuery):
    results = qdrant_repo.search(query.embedding, limit=query.limit)
    return results

# IMPROVED - WITH CACHING
from src.infrastructure.cache.redis import cache_result
import json

@router.post("/search")
@cache_result(ttl=3600)  # Cache for 1 hour
def search_vectors(query: SearchQuery):
    results = qdrant_repo.search(query.embedding, limit=query.limit)
    return results
```

**Add caching to**:
- [ ] Frequently executed vector searches
- [ ] Common entity lookups
- [ ] Graph traversals

### Task 4.4: Run Load Tests (2 hours)
**File**: `tests/load/locustfile.py` (UPDATE)

```python
# Current state - needs expansion
from locust import HttpUser, task, constant

class RAGBrainUser(HttpUser):
    wait_time = constant(1)
    
    @task
    def ingest_event(self):
        self.client.post(
            "/ingest/",
            json={"id": "test", "text": "test content", "metadata": {}},
            headers={"X-API-Key": "test_key"}
        )
    
    @task
    def search_vectors(self):
        self.client.post(
            "/vectors/search",
            json={"query_embedding": [0.1] * 384, "limit": 10}
        )
    
    @task
    def query_graph(self):
        self.client.post(
            "/graphs/query",
            json={"query": "MATCH (n) RETURN n LIMIT 10"}
        )

# Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000
```

**Run load test**:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 100 -r 10 -t 5m
```

### Task 4.5: Document Performance Baselines (1 hour)
**File**: `docs/PERFORMANCE.md` (CREATE NEW)

```markdown
# Performance Baselines

## Load Test Results (2026-01-16)

### Hardware
- CPU: 4 cores
- RAM: 8 GB
- Network: 1Gbps

### Results
- **Throughput**: 1,200 RPS (requests per second)
- **P50 Latency**: 45ms
- **P95 Latency**: 120ms
- **P99 Latency**: 250ms
- **Error Rate**: 0.1%

### Bottlenecks Identified
1. Neo4j graph traversal - optimize queries
2. Qdrant search - increase pool size
3. Kafka publish latency - check broker config

## Optimization Recommendations
...
```

---

## Phase 5: Testing & Validation (Week 4)
**Timeline**: 2-3 days | **Priority**: MEDIUM | **Owner**: Both

### Task 5.1: Integration Tests (2 hours)
**File**: `tests/integration/test_end_to_end.py` (UPDATE)

```python
"""End-to-end workflow tests."""

def test_complete_rag_workflow():
    """Test: Ingest → Extract → Store → Search → Retrieve."""
    # 1. Ingest event
    event_response = client.post("/ingest/", headers=auth_headers, json={...})
    assert event_response.status_code == 200
    
    # 2. Wait for processing
    time.sleep(2)
    
    # 3. Search vectors
    search_response = client.post("/vectors/search", headers=auth_headers, json={...})
    assert search_response.status_code == 200
    assert len(search_response.json()["results"]) > 0
    
    # 4. Query graph
    graph_response = client.post("/graphs/query", headers=auth_headers, json={...})
    assert graph_response.status_code == 200

def test_authentication_required():
    """All protected endpoints require authentication."""
    protected_endpoints = [
        ("POST", "/ingest/", {...}),
        ("POST", "/vectors/upsert", {...}),
        ("POST", "/graphs/create", {...}),
    ]
    
    for method, endpoint, data in protected_endpoints:
        if method == "POST":
            response = client.post(endpoint, json=data)  # No headers!
            assert response.status_code == 401
```

### Task 5.2: Resilience Tests (2 hours)
**File**: `tests/integration/test_resilience.py` (CREATE NEW)

```python
"""Test resilience patterns."""

def test_retry_on_transient_failure():
    """Verify retry mechanism works on transient failures."""
    # Simulate transient failure then success
    with patch('kafka.KafkaProducer.send') as mock_send:
        mock_send.side_effect = [KafkaError(), KafkaError(), "OK"]
        response = client.post("/ingest/", headers=auth_headers, json={...})
        assert response.status_code == 200
        assert mock_send.call_count == 3  # 2 retries + 1 success

def test_circuit_breaker_opens():
    """Verify circuit breaker protects against cascading failures."""
    with patch('kafka.KafkaProducer.send', side_effect=KafkaError()):
        # First 5 calls fail and hit circuit breaker threshold
        for i in range(5):
            response = client.post("/ingest/", headers=auth_headers, json={...})
            assert response.status_code == 503
        
        # 6th call should fail immediately (circuit open)
        response = client.post("/ingest/", headers=auth_headers, json={...})
        assert response.status_code == 503
```

### Task 5.3: Security Tests (2 hours)
**File**: `tests/integration/test_security.py` (CREATE NEW)

```python
"""Test security mechanisms."""

def test_endpoints_require_authentication():
    """All sensitive endpoints require auth."""
    endpoints = [
        ("POST", "/ingest/"),
        ("POST", "/vectors/upsert"),
        ("POST", "/graphs/create"),
    ]
    
    for method, endpoint in endpoints:
        if method == "POST":
            response = client.post(endpoint, json={})
            assert response.status_code == 401

def test_valid_token_accepted():
    """Valid JWT tokens are accepted."""
    token = create_test_token()
    response = client.post(
        "/ingest/",
        headers={"Authorization": f"Bearer {token}"},
        json={"id": "test", "text": "test"}
    )
    assert response.status_code == 200 or response.status_code == 400  # Not 401

def test_invalid_token_rejected():
    """Invalid tokens are rejected."""
    response = client.post(
        "/ingest/",
        headers={"Authorization": "Bearer invalid_token"},
        json={"id": "test", "text": "test"}
    )
    assert response.status_code == 401

def test_rate_limiting():
    """Rate limiting is enforced."""
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Make 61 requests (default limit is 60/minute)
    for i in range(61):
        response = client.post("/ingest/", headers=headers, json={...})
        if i < 60:
            assert response.status_code in [200, 400, 500]  # Not 429
        else:
            assert response.status_code == 429  # Too Many Requests
```

### Task 5.4: Run All Tests (1 hour)
```bash
# Run full test suite
pytest tests/ -v --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/ -v              # Unit tests
pytest tests/integration/ -v       # Integration tests
pytest tests/load/ -v              # Load tests
```

Expected output:
- ✅ 100+ tests passing
- ✅ >80% code coverage
- ✅ No warnings or deprecations

---

## Phase 6: Deployment & Documentation (Week 5)
**Timeline**: 2-3 days | **Priority**: MEDIUM | **Owner**: Both

### Task 6.1: Update Kubernetes Manifests (2 hours)
**File**: `k8s/deployment.yaml` (UPDATE)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: big-data-rag-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: big-data-rag:latest
        ports:
        - containerPort: 8000
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        
        # Resource limits
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        
        # Environment
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: NEO4J_MAX_POOL_SIZE
          value: "50"
        - name: QDRANT_TIMEOUT
          value: "30"
```

### Task 6.2: Create Deployment Guide (1 hour)
**File**: `docs/DEPLOYMENT.md` (UPDATE or CREATE NEW)

```markdown
# Deployment Guide

## Prerequisites
- Kubernetes cluster (1.24+)
- Docker registry access
- PostgreSQL for Airflow metadata
- Redis for caching

## Deployment Steps

### 1. Build & Push Image
```bash
docker build -t myregistry/big-data-rag:v1.0.0 .
docker push myregistry/big-data-rag:v1.0.0
```

### 2. Apply Kubernetes Manifests
```bash
kubectl apply -f k8s/
```

### 3. Verify Deployment
```bash
kubectl get pods -l app=big-data-rag-api
kubectl logs -l app=big-data-rag-api --tail=100 -f
```

### 4. Test API
```bash
kubectl port-forward svc/big-data-rag-api 8000:8000
curl http://localhost:8000/health/live
```
```

### Task 6.3: Update API Documentation (1 hour)
**File**: `docs/API.md` (UPDATE)

Add sections:
- [ ] Authentication requirements
- [ ] Rate limits
- [ ] Error codes
- [ ] Example requests with auth
- [ ] Health check endpoints
- [ ] Metrics endpoint

### Task 6.4: Create Operations Guide (1 hour)
**File**: `docs/OPERATIONS.md` (CREATE NEW)

```markdown
# Operations Guide

## Monitoring

### Prometheus Metrics
- Endpoint: `/metrics`
- Scrape interval: 15s
- Key metrics: request_count, request_duration, db_operation_latency

### Logs
- Format: JSON structured logs
- Send to: ELK/Datadog/CloudWatch
- Filter by: correlation_id, user_id, error_type

## Troubleshooting

### High latency
1. Check Neo4j pool saturation
2. Check Qdrant timeout settings
3. Review slow query logs

### High error rate
1. Check circuit breaker status
2. Verify database connectivity
3. Review error logs by type

### Memory leaks
1. Monitor goroutines (connections)
2. Check connection pool growth
3. Profile memory usage
```

---

## Summary of Changes

### Files to Create
- [ ] `src/api/handlers/health.py` - Health checks
- [ ] `docs/PERFORMANCE.md` - Performance baselines
- [ ] `docs/DEPLOYMENT.md` - Deployment guide
- [ ] `docs/OPERATIONS.md` - Operations runbook
- [ ] `tests/integration/test_resilience.py` - Resilience tests
- [ ] `tests/integration/test_security.py` - Security tests

### Files to Update (Large)
- [ ] `src/api/handlers/events.py` - Add auth + resilience
- [ ] `src/api/handlers/vectors.py` - Add auth + resilience + caching
- [ ] `src/api/handlers/graphs.py` - Add auth + resilience
- [ ] `src/api/handlers/hybrid.py` - Add auth + resilience
- [ ] `src/api/main.py` - Add metrics endpoint + health routes
- [ ] `src/utils/logging.py` - JSON structured logging
- [ ] `src/utils/config.py` - Add pool configurations
- [ ] `src/infrastructure/database/neo4j.py` - Optimize pooling
- [ ] `src/infrastructure/database/qdrant.py` - Optimize pooling
- [ ] `tests/load/locustfile.py` - Comprehensive load scenarios

### Requirements Changes
```
# Add to requirements.txt
python-json-logger>=2.0.0
```

---

## Success Criteria Checklist

### Week 1: Security ✅
- [ ] All POST/PUT/DELETE endpoints require authentication
- [ ] Authentication tests passing
- [ ] OpenAPI docs show auth requirement
- [ ] No hardcoded credentials in code

### Week 1-2: Resilience ✅
- [ ] Retry decorators applied to critical paths
- [ ] Circuit breakers protecting external services
- [ ] Resilience tests passing (retry + circuit breaker)
- [ ] Can survive and recover from failures

### Week 2-3: Observability ✅
- [ ] JSON logs in stdout
- [ ] `/metrics` endpoint operational
- [ ] Health checks responding
- [ ] Correlation IDs in all logs
- [ ] Can query logs by request ID

### Week 3-4: Performance ✅
- [ ] Connection pooling optimized
- [ ] Caching reducing database load
- [ ] Load test baseline established
- [ ] Documented performance characteristics

### Week 4: Testing ✅
- [ ] All integration tests passing
- [ ] Security tests passing
- [ ] Resilience tests passing
- [ ] 100+ tests total with >80% coverage

---

## Time Tracking Template

| Phase | Task | Estimate | Actual | Status |
|-------|------|----------|--------|--------|
| 1 | Security Review | 2h | | |
| 1 | Events Handler | 3h | | |
| 1 | Vectors Handler | 3h | | |
| 1 | Graphs Handler | 3h | | |
| 1 | Hybrid Handler | 2h | | |
| 1 | Testing | 2h | | |
| 2 | Resilience Review | 2h | | |
| ... | ... | ... | ... | ... |

---

**Next**: Start with Phase 1, Task 1.1 immediately!


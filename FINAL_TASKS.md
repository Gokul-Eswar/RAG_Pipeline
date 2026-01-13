# 🎯 FINAL ACTION PLAN - What's Left (10-15 Days)

**Status**: 75-80% complete, ready for final polish  
**Remaining Effort**: 10-15 days (1 developer)  
**Path to Production**: 2-3 weeks

---

## Priority 1: Search Endpoint Authentication (1-2 Hours)

### Decision: Are Search Endpoints Public or Private?

Currently **unprotected** (no auth required):
```python
# vectors.py - NO auth needed
@router.post("/search")
def search_vectors(request: SearchVectorsRequest):  # ← PUBLIC
    pass

# graphs.py - NO auth needed
@router.post("/node/find")  
def find_graph_node(request: NodeQueryRequest):  # ← PUBLIC
    pass
```

**Decision Options**:

**Option A: Keep Public (READ-ONLY = Safe)**
```python
# Leave as is - search is read-only, public is acceptable
@router.post("/search")
def search_vectors(request: SearchVectorsRequest):
    # No auth needed for read
    pass
```

**Option B: Require Authentication**
```python
# Add auth like other endpoints
@router.post("/search")
def search_vectors(
    request: SearchVectorsRequest,
    current_user: User = Depends(get_current_active_user)  # ← ADD THIS
):
    pass
```

**Option C: Read Permission (Future Enhancement)**
```python
# Add read-level permission (more complex)
@router.post("/search")
def search_vectors(
    request: SearchVectorsRequest,
    current_user: User = Depends(get_current_active_user),
    min_permission: str = Depends(lambda: "read")
):
    pass
```

### Action: Make This Decision
- [ ] Decide: Public, Private, or Permissioned?
- [ ] If public: Add comments explaining why
- [ ] If private: Add auth decorators to 3 search endpoints
- [ ] Update API docs with decision

**Affected Endpoints**:
1. `vectors.post("/search")` 
2. `graphs.post("/node/find")`
3. `vectors.post("/collection/info")`

---

## Priority 2: Add Structured Logging to Handlers (3-4 Hours)

### Current: Handlers are silent
```python
# events.py - NO logging
@router.post("/ingest/")
def ingest_event(request, current_user):
    producer = KafkaEventProducer()
    result = producer.publish(message)  # Silent success/failure!
    return {"status": "accepted"}
```

### Target: Add context-rich logging

**Pattern to Apply**:
```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

@router.post("/ingest/")
def ingest_event(request: IngestEventRequest, current_user: dict = Depends(get_current_active_user)):
    """Publish event with logging."""
    
    # 1. Log request start
    logger.info("Event ingestion started", extra={
        "event_id": request.id,
        "user": current_user.get("username", "unknown"),
        "text_length": len(request.text)
    })
    
    try:
        producer = KafkaEventProducer()
        result = producer.publish({
            "id": request.id,
            "text": request.text,
            "metadata": request.metadata or {},
        })
        
        # 2. Log success
        logger.info("Event published successfully", extra={
            "event_id": request.id,
            "status": "accepted"
        })
        
        return {
            "status": "accepted",
            "id": request.id,
            **result
        }
        
    except Exception as e:
        # 3. Log failure with details
        logger.error("Event ingestion failed", extra={
            "event_id": request.id,
            "error": str(e),
            "error_type": type(e).__name__,
            "user": current_user.get("username", "unknown")
        })
        raise HTTPException(
            status_code=503, 
            detail=f"Failed to ingest event: {str(e)}"
        )
```

### Files to Update (3-4 hours total)
1. **events.py** (30 min)
   - Log start, end, errors
   - Include event_id, user, timing

2. **vectors.py** (30 min)
   - Log upsert start/end
   - Log search queries
   - Log errors with collection info

3. **graphs.py** (30 min)
   - Log node create/find
   - Log relationship operations
   - Log errors with node info

4. **hybrid.py** (30 min)
   - Log search start/end
   - Log generation results
   - Log model availability

### Checklist for Each Handler
- [ ] Import `get_logger(__name__)`
- [ ] Log operation start (with key identifiers)
- [ ] Log operation end (with result)
- [ ] Log errors (with context)
- [ ] Use `extra={}` for custom fields
- [ ] Include timing if relevant

---

## Priority 3: Endpoint-Specific Rate Limits (2-3 Hours)

### Current: Global 60/minute for all endpoints
```python
# main.py - Global only
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
```

### Target: Tiered limits by operation criticality

**Pattern**:
```python
from src.api.main import limiter

# Sensitive operation - tight limit
@router.post("/ingest/")
@limiter.limit("10/minute")  # Only 10 ingestions per minute
def ingest_event(request, current_user):
    pass

# Data modification - medium limit
@router.post("/memory/upsert")
@limiter.limit("20/minute")  # 20 updates per minute
def upsert_vectors(request, current_user):
    pass

# Read operation - loose limit
@router.post("/memory/search")
@limiter.limit("100/minute")  # 100 searches per minute (or no limit)
def search_vectors(request):
    pass
```

### Suggested Limits
```
POST /ingest/          → 10/minute  (most expensive)
POST /memory/upsert    → 20/minute  (expensive)
POST /graph/node       → 20/minute  (expensive)
POST /memory/search    → 100/minute (cheap, read-only)
POST /graph/node/find  → 100/minute (cheap, read-only)
GET  /health/*         → Unlimited  (internal)
GET  /metrics          → Unlimited  (internal)
```

### Files to Update (2-3 hours)
1. **handlers/events.py** - Add `@limiter.limit("10/minute")` to ingest
2. **handlers/vectors.py** - Add limits to upsert (20), search (100)
3. **handlers/graphs.py** - Add limits to create (20), find (100)
4. **handlers/hybrid.py** - Add limit to generate (20)

### Get Limiter in Handlers
```python
from fastapi import Request

@router.post("/ingest/")
@limiter.limit("10/minute")
def ingest_event(request: Request, ...):  # Need Request param for limiter to work
    pass
```

---

## Priority 4: Specific Error Handling (4-6 Hours)

### Current: Catches all exceptions as 500
```python
try:
    result = operation()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")
```

### Target: Differentiate error types

**Pattern**:
```python
from circuitbreaker import CircuitBreakerError
from neo4j.exceptions import ServiceUnavailable
from src.utils.exceptions import AppError

try:
    result = operation()
    
except CircuitBreakerError:
    # Service is overloaded/down
    logger.warning("Circuit breaker opened", extra={"operation": "ingest"})
    raise HTTPException(
        status_code=503,
        detail="Service temporarily unavailable - too many failures"
    )
    
except TimeoutError:
    # Operation took too long
    logger.warning("Operation timeout", extra={"operation": "ingest"})
    raise HTTPException(
        status_code=504,
        detail="Operation timeout - please try again"
    )
    
except ServiceUnavailable:
    # Database is down
    logger.error("Database unavailable", extra={"operation": "ingest"})
    raise HTTPException(
        status_code=502,
        detail="Backend database temporarily unavailable"
    )
    
except ValidationError as e:
    # Input invalid
    logger.warning("Validation error", extra={"operation": "ingest", "errors": str(e)})
    raise HTTPException(
        status_code=400,
        detail=f"Invalid input: {str(e)}"
    )
    
except KafkaError as e:
    # Message broker error
    logger.error("Kafka error", extra={"operation": "ingest", "error": str(e)})
    raise HTTPException(
        status_code=502,
        detail="Message broker error - please try again"
    )
    
except Exception as e:
    # Unexpected error
    logger.error("Unexpected error", extra={
        "operation": "ingest",
        "error": str(e),
        "error_type": type(e).__name__
    })
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
```

### Files to Update (4-6 hours)
1. **events.py** (1h) - Kafka/Circuit/Timeout errors
2. **vectors.py** (1h) - Qdrant/Circuit/Timeout errors
3. **graphs.py** (1h) - Neo4j/Circuit/Timeout errors
4. **hybrid.py** (1h) - Embedding/LLM/timeout errors
5. **api/middleware/error_handlers.py** (1h) - Global handlers

### HTTP Status Code Mapping
```
200 - Success
400 - Validation error (client fault)
401 - Authentication failed
403 - Permission denied
404 - Not found
409 - Conflict (duplicate)
429 - Rate limit exceeded
500 - Internal server error
502 - Bad gateway (upstream service error)
503 - Service unavailable (circuit breaker open)
504 - Gateway timeout (operation timeout)
```

---

## Priority 5: Load Testing (4-6 Hours)

### Current: Locust installed, not used
```python
# tests/load/locustfile.py exists but minimal
```

### Target: Realistic scenarios with baselines

**Create Comprehensive Load Test**:
```python
# tests/load/locustfile.py

from locust import HttpUser, task, between
from random import randint

class RAGUserScenarios(HttpUser):
    """Realistic user scenarios."""
    
    wait_time = between(1, 3)  # 1-3 seconds between requests
    
    def on_start(self):
        """Authenticate once."""
        # Get token for authenticated requests
        response = self.client.post("/auth/token", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)  # 10x more likely than others
    def search_vectors(self):
        """Read-heavy scenario."""
        query_vector = [0.1] * 384  # Dummy embedding
        self.client.post(
            "/memory/search",
            json={"query_vector": query_vector, "limit": 10},
            headers=self.headers,
            name="vector_search"
        )
    
    @task(5)  # 5x likely
    def search_graph(self):
        """Graph query."""
        self.client.post(
            "/graph/node/find",
            json={"label": "Entity", "properties": {"name": f"entity_{randint(1,100)}"}},
            headers=self.headers,
            name="graph_search"
        )
    
    @task(3)  # 3x likely
    def ingest_event(self):
        """Write operation."""
        self.client.post(
            "/ingest/",
            json={
                "id": f"event_{randint(1,10000)}",
                "text": f"Sample text {randint(1,1000)}",
                "metadata": {"source": "test"}
            },
            headers=self.headers,
            name="ingest"
        )
    
    @task(2)  # 2x likely
    def upsert_vectors(self):
        """Vector update."""
        vectors = [{
            "id": randint(1, 1000),
            "vector": [0.1 * i for i in range(384)],
            "payload": {"text": f"doc_{i}"}
        } for i in range(10)]
        self.client.post(
            "/memory/upsert",
            json={"vectors": vectors},
            headers=self.headers,
            name="upsert"
        )
    
    @task(1)  # Least likely
    def create_node(self):
        """Graph write."""
        self.client.post(
            "/graph/node",
            json={
                "label": "Entity",
                "properties": {
                    "name": f"entity_{randint(1,1000)}",
                    "type": "test"
                }
            },
            headers=self.headers,
            name="create_node"
        )
```

### How to Run
```bash
# Start the app
python run.py api

# In another terminal, run load test
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    -u 100 \              # 100 concurrent users
    -r 10 \               # Ramp up 10 users/sec
    -t 5m \               # Run for 5 minutes
    --headless            # No UI

# Expected output:
# Type     Name      Request   Count   Mean   Min    Max
# POST     ingest    /ingest/  1200    45ms   10ms   200ms
# POST     search    /search   2400    30ms   5ms    150ms
```

### Document Results
```markdown
# Load Test Baseline - January 13, 2026

## Test Parameters
- Users: 100 concurrent
- Ramp-up: 10 users/sec
- Duration: 5 minutes
- Total Requests: 5000+

## Results
- Throughput: 1000+ RPS
- P50 Latency: 45ms
- P95 Latency: 120ms
- P99 Latency: 250ms
- Error Rate: 0.1%

## Bottlenecks
1. Vector search - takes 40ms average
2. Node creation - takes 60ms average
3. Kafka publish - takes 35ms average

## Recommendations
1. Add caching for frequent searches
2. Batch vector inserts
3. Optimize Neo4j queries
```

---

## Priority 6: Test Integration Updates (2-4 Hours)

### Verify Tests Pass with Current Setup
```bash
# Run all tests
pytest tests/ -v

# Run specific suites
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/load/ -v
```

### Update Integration Tests if Needed
```python
# tests/integration/test_api_endpoints.py

def test_ingest_requires_auth():
    """Verify auth is enforced."""
    response = client.post("/ingest/", json={
        "id": "test",
        "text": "test"
    })
    assert response.status_code == 401  # Unauthorized

def test_ingest_with_valid_token():
    """Verify ingest works with token."""
    token = get_test_token()
    response = client.post(
        "/ingest/",
        json={"id": "test", "text": "test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_search_vectors():
    """Search endpoint test."""
    response = client.post("/memory/search", json={
        "query_vector": [0.1] * 384,
        "limit": 10
    })
    # Decide: should this be 200 (public) or 401 (private)?
    assert response.status_code in [200, 401]
```

---

## Week-by-Week Plan

### Week 1 (Days 1-5)
- [ ] Day 1: Decide on search endpoint auth
- [ ] Days 2-3: Add structured logging to all handlers
- [ ] Days 4-5: Add endpoint-specific rate limits

### Week 2 (Days 6-10)
- [ ] Days 6-7: Implement specific error handling
- [ ] Days 8-9: Run load tests and document
- [ ] Day 10: Update and verify tests pass

### Week 3 (Days 11-15)
- [ ] Days 11-12: Polish and fix any issues
- [ ] Days 13-14: Performance optimization based on load test
- [ ] Day 15: Final validation and documentation

---

## Final Checklist

### Authentication
- [x] JWT implemented
- [x] Applied to ingest/upsert/create endpoints
- [ ] Decision made on search endpoint auth
- [ ] Applied to search if decided
- [ ] API docs updated

### Logging
- [x] JSON logging configured
- [ ] Actually used in all handlers
- [ ] Correlation IDs in all logs
- [ ] Error details logged

### Rate Limiting
- [x] Global limit configured
- [ ] Endpoint-specific limits added
- [ ] Sensitive ops have tight limits
- [ ] Read ops have loose limits

### Error Handling
- [ ] Specific handlers for different errors
- [ ] Circuit breaker → 503
- [ ] Timeout → 504
- [ ] Upstream errors → 502
- [ ] Validation errors → 400

### Testing
- [ ] All tests pass with changes
- [ ] Load test baseline established
- [ ] Performance targets documented
- [ ] Bottlenecks identified

### Documentation
- [ ] API docs updated
- [ ] Deployment guide updated
- [ ] Operations guide updated
- [ ] Load test results documented

---

## Success Criteria

✅ **Done When**:
- All handlers have structured logging
- Search endpoints auth decision made and implemented
- Rate limits working on all endpoints
- Error handling specific to error types
- Load test baseline established
- All tests passing
- Documentation updated

---

**Start with Priority 1 today.  
Each priority is 1-2 days work.**

**You'll be 90%+ production-ready in 2 weeks.**


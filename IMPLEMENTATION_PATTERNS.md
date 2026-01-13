# Implementation Patterns - 6 Remaining Items

**Purpose**: Code examples and patterns for each remaining item  
**Read this**: After reading CORRECTED_STATUS.md  
**Use this**: As a template when implementing each item  

---

## Item 1: Search Endpoint Auth Decision (1-2 hours)

### Current Status
Search endpoints are currently public and read-only (safe):
```python
# src/api/handlers/vectors.py
@router.post("/search")
def search_vectors(request: SearchVectorsRequest):
    # No @Depends(get_current_active_user) - This is intentional (read-only)
    pass
```

### Decision Framework

**Option A: Keep Public** (RECOMMENDED ✅)
- Read-only operations are inherently safe
- Aligns with REST best practices
- Allows public API access
- Common for search/query endpoints

**Option B: Add Authentication**
- More restrictive access control
- Requires API token for all requests
- Might limit public usage

### Implementation Pattern

**If you choose Option A** (Keep Public):
```python
# src/api/handlers/vectors.py - Line 45

# Add this comment to document the decision
@router.post("/search")
def search_vectors(request: SearchVectorsRequest):
    """
    Search for similar vectors in the collection.
    
    NOTE: This endpoint is intentionally public and requires NO authentication
    because it performs read-only operations. Authentication is required only
    for data modification operations (upsert/delete).
    
    Args:
        request: SearchVectorsRequest containing query vector and parameters
        
    Returns:
        SearchVectorsResponse with similar vectors
    """
    # Implementation
    pass
```

### Files to Document
1. `src/api/handlers/vectors.py` - search_vectors() endpoint
2. `src/api/handlers/vectors.py` - collection/info endpoint  
3. `src/api/handlers/graphs.py` - find_graph_node() endpoint

### Checklist
- [ ] Decision made (A or B)
- [ ] Comment added to each endpoint
- [ ] README.md updated with auth policy
- [ ] API documentation updated

---

## Item 2: Handler Logging Integration (3-4 hours)

### Current Status
Logging infrastructure exists but handlers don't use it:
```python
# src/utils/logging.py - Complete setup exists
# but handlers don't call it
```

### Implementation Pattern

**Pattern 1: Success Path Logging**
```python
# src/api/handlers/events.py

from src.utils.logging import setup_logger
from src.models.domain import User

logger = setup_logger(__name__)

@router.post("/ingest/")
def ingest_event(
    request: IngestEventRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Ingest a single event."""
    event_id = request.event_id or str(uuid.uuid4())
    
    # Log start with context
    logger.info(
        "Event ingestion started",
        extra={
            "event_id": event_id,
            "user": current_user.username,
            "source": request.source
        }
    )
    
    try:
        # Business logic
        producer = KafkaEventProducer()
        result = producer.publish(message=request.dict())
        
        # Log success
        logger.info(
            "Event published successfully",
            extra={
                "event_id": event_id,
                "duration_ms": compute_duration(),
                "messages_sent": len(result)
            }
        )
        
        return {"status": "accepted", "event_id": event_id}
        
    except Exception as e:
        # Log failure
        logger.error(
            "Event ingestion failed",
            extra={
                "event_id": event_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(status_code=503, detail="Message broker unavailable")
```

**Pattern 2: Search Path Logging**
```python
# src/api/handlers/vectors.py

@router.post("/search")
def search_vectors(request: SearchVectorsRequest):
    """Search for similar vectors."""
    search_id = str(uuid.uuid4())
    
    logger.info(
        "Vector search started",
        extra={
            "search_id": search_id,
            "collection": request.collection,
            "top_k": request.top_k
        }
    )
    
    try:
        repo = QdrantVectorRepository()
        results = repo.search(
            collection=request.collection,
            vector=request.vector,
            top_k=request.top_k
        )
        
        logger.info(
            "Vector search completed",
            extra={
                "search_id": search_id,
                "results_count": len(results),
                "duration_ms": compute_duration()
            }
        )
        
        return SearchVectorsResponse(results=results)
        
    except Exception as e:
        logger.error(
            "Vector search failed",
            extra={"search_id": search_id, "error": str(e)}
        )
        raise
```

### Implementation Checklist
**events.py** (45 min):
- [ ] Import setup_logger
- [ ] Add logger = setup_logger(__name__)
- [ ] Log start of ingest_event
- [ ] Log successful publish
- [ ] Log failures with error details

**vectors.py** (45 min):
- [ ] Log search start with request params
- [ ] Log search success with result count
- [ ] Log failures
- [ ] Add logging to upsert endpoint

**graphs.py** (45 min):
- [ ] Log create_node start
- [ ] Log success with created node ID
- [ ] Log failures
- [ ] Add to find_node endpoint

**hybrid.py** (45 min):
- [ ] Log search start
- [ ] Log generation start
- [ ] Log combined results
- [ ] Log failures

**Testing** (1 hour):
- [ ] Verify logs appear in output
- [ ] Check JSON formatting
- [ ] Validate correlation IDs included
- [ ] Test error logging

---

## Item 3: Error Response Specificity (4-6 hours)

### Current Status
Most errors return generic 500:
```python
# Current (all exceptions → 500)
try:
    result = operation()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

### Implementation Pattern

**Pattern 1: Generic Handler Wrapper**
```python
# src/api/handlers/base.py (new file)

from fastapi import HTTPException
from src.utils.exceptions import (
    CircuitBreakerError,
    TimeoutError,
    DatabaseError,
    ValidationError,
    AuthenticationError
)

def handle_operation_errors(func):
    """Decorator to map custom exceptions to HTTP responses."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CircuitBreakerError:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. Please retry later."
            )
        except TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Operation timed out. Please try a simpler query."
            )
        except DatabaseError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Database error: {str(e)}"
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request: {str(e)}"
            )
        except AuthenticationError:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    return wrapper
```

**Pattern 2: Direct Implementation**
```python
# src/api/handlers/events.py

@router.post("/ingest/")
def ingest_event(request: IngestEventRequest, current_user: User = Depends(get_current_active_user)):
    """Ingest a single event."""
    try:
        producer = KafkaEventProducer()
        result = producer.publish(message=request.dict())
        return {"status": "accepted", "event_id": request.event_id}
        
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Message broker temporarily unavailable. Retrying..."
        )
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Message broker timeout. Message might be queued."
        )
    except ConnectionError as e:
        logger.error(f"Kafka connection failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Message broker connection failed"
        )
    except Exception as e:
        logger.error(f"Event ingestion error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Event ingestion failed"
        )
```

### HTTP Status Code Mapping
```
200 OK              - Successful operations
201 Created         - Resource created
202 Accepted        - Event accepted for processing
400 Bad Request     - Validation errors
401 Unauthorized    - Authentication required
403 Forbidden       - Permission denied
404 Not Found       - Resource not found
429 Too Many        - Rate limit exceeded
500 Internal Error  - Unexpected errors
502 Bad Gateway     - Database/service error
503 Unavailable     - Circuit breaker open
504 Gateway Timeout - Operation timeout
```

### Implementation Checklist
- [ ] Create custom exception types if needed
- [ ] Add error handling to events.py
- [ ] Add error handling to vectors.py
- [ ] Add error handling to graphs.py
- [ ] Add error handling to hybrid.py
- [ ] Test each error condition
- [ ] Update API documentation

---

## Item 4: Per-Endpoint Rate Limits (2-3 hours)

### Current Status
Global 60/minute rate limit on all endpoints:
```python
# src/api/main.py
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
```

### Implementation Pattern

**Pattern 1: Apply to Expensive Operations**
```python
# src/api/handlers/events.py

from src.api.main import limiter

@router.post("/ingest/")
@limiter.limit("10/minute")  # Expensive: writes to Kafka
def ingest_event(request: IngestEventRequest, current_user: User = Depends(get_current_active_user)):
    """Publish single event (10/minute limit)."""
    pass

@router.post("/ingest_batch/")
@limiter.limit("5/minute")  # Very expensive: multiple writes
def ingest_batch(request: IngestBatchRequest, current_user: User = Depends(get_current_active_user)):
    """Publish multiple events (5/minute limit)."""
    pass
```

**Pattern 2: Apply to Vector Operations**
```python
# src/api/handlers/vectors.py

@router.post("/upsert")
@limiter.limit("20/minute")  # Moderate: vector upsert
def upsert_vectors(request: UpsertRequest, current_user: User = Depends(get_current_active_user)):
    """Upsert vectors (20/minute limit)."""
    pass

@router.post("/search")
@limiter.limit("100/minute")  # Cheap: read-only search
def search_vectors(request: SearchVectorsRequest):
    """Search vectors (100/minute limit)."""
    pass
```

**Pattern 3: Apply to Graph Operations**
```python
# src/api/handlers/graphs.py

@router.post("/node/create")
@limiter.limit("20/minute")  # Graph writes
def create_node(request: CreateNodeRequest, current_user: User = Depends(get_current_active_user)):
    """Create node (20/minute limit)."""
    pass

@router.post("/node/find")
@limiter.limit("100/minute")  # Graph reads
def find_node(request: NodeQueryRequest):
    """Find node (100/minute limit)."""
    pass
```

### Suggested Rate Limits
```
Ingest events:         10/minute  (Kafka write, expensive)
Ingest batch:          5/minute   (Multiple Kafka writes, very expensive)
Upsert vectors:        20/minute  (Vector DB write)
Search vectors:        100/minute (Vector DB read, cheap)
Create node:           20/minute  (Graph write)
Find node:             100/minute (Graph read)
Search/generate:       20/minute  (LLM operations, expensive)
Health checks:         Unlimited  (Infrastructure)
Metrics:               Unlimited  (Monitoring)
```

### Implementation Checklist
- [ ] Import limiter from main.py
- [ ] Add @limiter.limit() to ingest operations
- [ ] Add @limiter.limit() to vector operations
- [ ] Add @limiter.limit() to graph operations
- [ ] Add @limiter.limit() to hybrid operations
- [ ] Test rate limit responses (429 Too Many Requests)
- [ ] Update API documentation

---

## Item 5: Load Testing Execution (4-6 hours)

### Current Status
Locust framework installed but not executed:
```
tests/load/locustfile.py exists but likely incomplete
```

### Implementation Pattern

**Basic Load Test**
```python
# tests/load/locustfile.py

from locust import HttpUser, task, between
import json

class BigDataRAGUser(HttpUser):
    """Simulates a user interacting with Big Data RAG API."""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Setup: login and get token."""
        response = self.client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(1)
    def search_vectors(self):
        """Task: Search vectors (read-only)."""
        self.client.post(
            "/vectors/search",
            json={
                "collection": "documents",
                "vector": [0.1, 0.2, 0.3, ...],
                "top_k": 10
            }
        )
    
    @task(1)
    def find_nodes(self):
        """Task: Find graph nodes (read-only)."""
        self.client.post(
            "/graphs/node/find",
            json={"label": "Document", "limit": 20}
        )
    
    @task(2)
    def ingest_event(self):
        """Task: Ingest event (write operation)."""
        self.client.post(
            "/events/ingest/",
            json={
                "source": "test",
                "event_type": "document_added",
                "data": {"doc_id": "test123"}
            },
            headers=self.headers
        )
```

### Running the Load Test

**Command**:
```bash
# Terminal
cd d:\GOKUL_ESWAR\Codebase\Big_Data_RAG
locust -f tests/load/locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

**Locust Web UI**:
- Opens at http://localhost:8089
- Start with small number of users (10)
- Gradually increase to peak (100+)
- Monitor response times and failures

### Results to Document
```
Test Duration:       [X] minutes
Peak Users:          [X]
Average Response:    [X] ms
P95 Response:        [X] ms
P99 Response:        [X] ms
Error Rate:          [X]%
Throughput:          [X] requests/second
```

### Implementation Checklist
- [ ] Review locustfile.py
- [ ] Create realistic load scenarios
- [ ] Run with 10 users
- [ ] Run with 50 users
- [ ] Run with 100 users
- [ ] Document baseline metrics
- [ ] Identify bottlenecks
- [ ] Create load_testing_report.md

---

## Item 6: Test Integration Updates (2-4 hours)

### Current Status
Tests exist but may need updates for authentication:

```python
# Current test may not include auth headers
def test_ingest_event():
    response = client.post("/events/ingest/", json={...})
    # This will fail if endpoint now requires authentication
```

### Implementation Pattern

**Pattern 1: Get Auth Token in Fixture**
```python
# tests/conftest.py (update existing fixture)

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for protected endpoints."""
    # Create test user
    user_response = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "testpass"}
    )
    
    # Login and get token
    login_response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass"}
    )
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def authenticated_client(client, auth_headers):
    """Client with authentication headers pre-configured."""
    client.headers = auth_headers
    return client
```

**Pattern 2: Update Existing Tests**
```python
# tests/test_api_endpoints.py (update existing)

def test_ingest_event(authenticated_client):  # Use authenticated_client
    """Test event ingestion with authentication."""
    response = authenticated_client.post(
        "/events/ingest/",
        json={
            "source": "test",
            "event_type": "document_added",
            "data": {"doc_id": "test123"}
        }
    )
    assert response.status_code == 202  # Accepted
    assert response.json()["status"] == "accepted"

def test_ingest_without_auth(client):
    """Test that event ingestion fails without authentication."""
    response = client.post(
        "/events/ingest/",
        json={...}
    )
    assert response.status_code == 401  # Unauthorized

def test_search_public(client):
    """Test that search is public (no auth required)."""
    response = client.post(
        "/vectors/search",
        json={...}
    )
    assert response.status_code == 200  # OK (no auth needed)
```

### Test Categories to Update

1. **Protected Endpoint Tests**
   - Add authentication headers
   - Test with valid token
   - Test without token (expect 401)

2. **Public Endpoint Tests**
   - Verify no auth required
   - Ensure 200 response without token

3. **Error Condition Tests**
   - Test 400 (validation errors)
   - Test 401 (auth errors)
   - Test 503 (service unavailable)
   - Test 504 (timeout)

### Implementation Checklist
- [ ] Review existing tests
- [ ] Create auth_headers fixture
- [ ] Create authenticated_client fixture
- [ ] Update protected endpoint tests
- [ ] Add negative auth tests
- [ ] Update public endpoint tests
- [ ] Run full test suite
- [ ] Verify all tests pass

---

## 🎯 Implementation Priority

**Fastest wins** (do these first):
1. Search endpoint auth decision (1-2h) ← Just a decision
2. Per-endpoint rate limits (2-3h) ← Copy/paste pattern

**Medium effort**:
3. Handler logging (3-4h) ← Repetitive but straightforward
4. Test auth updates (2-4h) ← Fix existing tests

**Longer tasks**:
5. Error response specificity (4-6h) ← Methodical refactoring
6. Load testing (4-6h) ← Run and document

**Total**: 10-15 days working solo

---

## 📋 Code Template Summary

| Item | Template | Time |
|------|----------|------|
| Search auth | Comment template | 0.5h |
| Handler logging | Decorator + logger.info/error | 3-4h |
| Error handling | try/except with specific codes | 4-6h |
| Rate limits | @limiter.limit("X/minute") | 2-3h |
| Load test | locust.HttpUser subclass | 4-6h |
| Test updates | auth_headers fixture | 2-4h |

---

**Ready to start implementing?** Pick item #1 (search endpoint auth) - it's the quickest win! 🚀

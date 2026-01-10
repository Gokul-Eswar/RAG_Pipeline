# Track Plan: Enterprise Security Integration (Phase 2)

**Status**: In Progress
**Track ID**: enterprise_security_20260110
**Goal**: Implement comprehensive security controls including JWT authentication, rate limiting, and secure credential management.

## Tasks

- [ ] **Task 1: Secure Credentials & Environment**
    - [ ] Generate strong SECRET_KEY.
    - [ ] Update `src/utils/config.py` to require critical env vars.
    - [ ] Remove hardcoded credentials from `src/infrastructure/database/neo4j.py`.
    - [ ] Update `.env.example`.

- [ ] **Task 2: Implement Rate Limiting & CORS**
    - [ ] Install `slowapi`.
    - [ ] Configure `CORSMiddleware` in `src/api/main.py`.
    - [ ] Configure `Limiter` in `src/api/main.py`.
    - [ ] Apply default rate limits.

- [ ] **Task 3: Integrate JWT Authentication**
    - [ ] Ensure `src/api/security.py` is robust (verify hashing, token generation).
    - [ ] Create `src/api/handlers/auth.py` with login endpoint.
    - [ ] Register auth router in `src/api/main.py`.
    - [ ] Add `Depends(get_current_active_user)` to `src/api/handlers/events.py`.
    - [ ] Add `Depends(get_current_active_user)` to `src/api/handlers/vectors.py`.
    - [ ] Add `Depends(get_current_active_user)` to `src/api/handlers/graphs.py`.

- [ ] **Task 4: API Key Management**
    - [ ] Implement API key hashing and validation logic in `src/api/handlers/auth.py`.
    - [ ] Create endpoint to generate API keys.
    - [ ] Create middleware or dependency to validate API keys.

- [ ] **Task 5: Verification**
    - [ ] Run unit tests for auth.
    - [ ] Verify endpoints return 401 without auth.
    - [ ] Verify rate limiting blocks excessive requests.

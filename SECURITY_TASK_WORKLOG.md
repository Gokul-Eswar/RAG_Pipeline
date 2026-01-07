# Security Hardening Worklog

## Status: 🟡 In Progress (Paused until 2026-01-08)

### Completed Tasks (2026-01-07)
- [x] Initial codebase analysis for security gaps.
- [x] Updated `requirements.txt` with security dependencies:
    - `python-jose[cryptography]` (JWT handling)
    - `passlib[bcrypt]` (Password hashing)
    - `python-multipart` (OAuth2 form handling)
    - `slowapi` (Rate limiting)

### Planned Tasks (Tomorrow)

#### 1. Configuration & Secrets Management
- Update `src/utils/config.py` to include:
    - `SECRET_KEY` (for JWT)
    - `ACCESS_TOKEN_EXPIRE_MINUTES`
    - `API_KEYS` list
    - `CORS_ORIGINS`

#### 2. Security Module Implementation
- Create `src/api/security.py`:
    - JWT creation and validation logic.
    - Password hashing utilities.
    - API Key validation.
    - OAuth2 password bearer schemes.

#### 3. Middleware & Protection
- Implement Rate Limiting in `src/api/main.py` using `slowapi`.
- Configure CORS middleware.
- Create an `/auth` router for token generation.
- Add `Depends(get_current_user)` or `Depends(verify_api_key)` to sensitive routes:
    - `POST /ingest/`
    - `POST /memory/*`
    - `POST /graph/*`

#### 4. Verification
- Write tests for authentication and rate limiting.
- Verify SSL/TLS requirements for production.

---
*Note: Dependencies added to `requirements.txt` still need to be installed in the environment (`pip install -r requirements.txt`).*

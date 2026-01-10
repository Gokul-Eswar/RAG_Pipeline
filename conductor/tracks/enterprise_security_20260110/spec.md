# Track Specification: Enterprise Security Integration

## Context
The system currently lacks essential security controls for a production environment. Credentials are hardcoded, endpoints are open, and there is no protection against abuse. This track implements Phase 2 of the Enterprise Readiness Plan.

## Requirements

### 1. Authentication (JWT)
- **Mechanism**: OAuth2 with Password (and Client Credentials flow for M2M if needed, but sticking to User/Password + API Key for now).
- **Token**: JWT (JSON Web Token) containing `sub` (username/user_id) and `exp` (expiration).
- **Scope**: All data-modifying endpoints (POST, PUT, DELETE) and sensitive GET endpoints must require authentication.
- **Login**: A `/auth/token` endpoint to exchange credentials for a bearer token.

### 2. Rate Limiting
- **Tool**: `slowapi` (based on limits).
- **Policy**:
    - Unauthenticated: 10 requests/minute (or strictly blocked if auth is mandatory).
    - Authenticated: 100 requests/minute per user.
- **Headers**: Standard `X-RateLimit-*` headers should be returned.

### 3. CORS (Cross-Origin Resource Sharing)
- **Policy**: configured via `Config.CORS_ORIGINS`.
- **Defaults**: Allow `*` for now, but configured via env var.

### 4. Credential Management
- **Rule**: NO hardcoded passwords in code.
- **Implementation**:
    - `NEO4J_AUTH` must come from env vars.
    - `SECRET_KEY` must be loaded from env vars and fail if default/missing in production.

### 5. API Keys
- **Purpose**: For service accounts or programmatic access where JWT flows are cumbersome.
- **Security**: Store hashed keys, not plaintext.
- **Endpoints**:
    - `POST /auth/api-key`: Generate a new key (returns plaintext once).
    - Usage: `X-API-Key` header.

## Technical Design

### `src/api/main.py`
- Initialize `Limiter`.
- Add `CORSMiddleware`.
- Include `auth_router`.

### `src/api/security.py`
- Existing module seems mostly complete but needs review.
- Add `get_api_key_user` dependency if API keys map to users.

### `src/api/handlers/auth.py`
- New file.
- `POST /token`: Standard OAuth2 login.
- `POST /api-key`: Generate key.

### `src/utils/config.py`
- Add validation logic in `__init__` or post-init to ensure `SECRET_KEY` is set.

# Agent A — Task 03: FastAPI Skeleton + Auth

## Mission
Create the FastAPI application entry point with CORS configuration, router includes, health endpoint, authentication helpers for extracting user role from Supabase JWT, request logging middleware, and basic error handling.

## Context
Day 1 task, follows Task 02 (schema). This is the foundation every API endpoint builds on. Auth helpers must match the RLS policy approach — the JWT contains `user_metadata.role` which maps to `talent_partner`, `client`, or `admin`. All subsequent API tasks import from `api/auth.py` for role-based access control.

## Prerequisites
- Task 01 complete (contracts, config, requirements)
- Task 02 complete (schema exists, `user_role` enum defined in DB)
- `backend/requirements.txt` installed

## Checklist
- [ ] Create `backend/main.py` with FastAPI app, CORS, lifespan, router includes
- [ ] Create `backend/api/__init__.py`
- [ ] Create `backend/api/auth.py` with JWT decoding, role extraction, dependency injection
- [ ] Create `backend/api/deps.py` with shared dependencies (Supabase client, DB session)
- [ ] Add health check endpoint at `GET /health`
- [ ] Add request logging middleware
- [ ] Add global exception handlers (422, 404, 500)
- [ ] Create `backend/tests/test_api.py` with health endpoint test
- [ ] Verify: `uvicorn main:app --reload` starts without errors
- [ ] Verify: `GET /health` returns 200
- [ ] Commit

## Implementation Details

### FastAPI App (`backend/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uuid

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recruittech")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("RecruitTech API starting up")
    yield
    logger.info("RecruitTech API shutting down")


app = FastAPI(
    title="RecruitTech API",
    description="Recruitment platform backend — Mothership engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Request Logging Middleware ----

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(
        f"[{request_id}] {request.method} {request.url.path} started"
    )

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"completed {response.status_code} in {duration_ms:.1f}ms"
    )

    response.headers["X-Request-ID"] = request_id
    return response


# ---- Global Exception Handlers ----

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found", "path": request.url.path},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ---- Health Check ----

@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint. Returns 200 if API is running."""
    return {
        "status": "healthy",
        "service": "recruittech-api",
        "version": "0.1.0",
    }


# ---- Router Includes ----
# Imported here, added as routers are built in subsequent tasks.
# Each router file defines an APIRouter; we include them with prefixes.

# from api.candidates import router as candidates_router
# from api.roles import router as roles_router
# from api.matches import router as matches_router
# from api.collections import router as collections_router
# from api.handoffs import router as handoffs_router
# from api.quotes import router as quotes_router
# from api.copilot import router as copilot_router
# from api.signals import router as signals_router
# from api.admin import router as admin_router

# app.include_router(candidates_router, prefix="/api/candidates", tags=["candidates"])
# app.include_router(roles_router, prefix="/api/roles", tags=["roles"])
# app.include_router(matches_router, prefix="/api/matches", tags=["matches"])
# app.include_router(collections_router, prefix="/api/collections", tags=["collections"])
# app.include_router(handoffs_router, prefix="/api/handoffs", tags=["handoffs"])
# app.include_router(quotes_router, prefix="/api/quotes", tags=["quotes"])
# app.include_router(copilot_router, prefix="/api/copilot", tags=["copilot"])
# app.include_router(signals_router, prefix="/api/signals", tags=["signals"])
# app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
```

### Auth Helpers (`backend/api/auth.py`)

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from uuid import UUID
from pydantic import BaseModel
import logging

from config import settings
from contracts.shared import UserRole

logger = logging.getLogger("recruittech.auth")

# Supabase JWT uses HS256 with the JWT secret
# For local dev, the JWT secret is derived from the Supabase project
SUPABASE_JWT_SECRET = settings.supabase_key  # anon key used for verification in PoC
ALGORITHM = "HS256"

security = HTTPBearer()


class CurrentUser(BaseModel):
    """Represents the authenticated user extracted from JWT."""
    id: UUID
    email: str
    role: UserRole


def decode_supabase_jwt(token: str) -> dict:
    """Decode and validate a Supabase JWT token.

    Supabase JWTs contain:
    - sub: user UUID
    - email: user email
    - user_metadata: { role: "talent_partner" | "client" | "admin" }
    """
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> CurrentUser:
    """FastAPI dependency: extract and validate current user from JWT.

    Usage in routes:
        @router.get("/something")
        async def something(user: CurrentUser = Depends(get_current_user)):
            ...
    """
    payload = decode_supabase_jwt(credentials.credentials)

    user_id = payload.get("sub")
    email = payload.get("email", "")
    user_metadata = payload.get("user_metadata", {})
    role_str = user_metadata.get("role", "talent_partner")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")

    try:
        role = UserRole(role_str)
    except ValueError:
        raise HTTPException(status_code=401, detail=f"Invalid role: {role_str}")

    return CurrentUser(id=UUID(user_id), email=email, role=role)


def require_role(*allowed_roles: UserRole):
    """Dependency factory: restrict endpoint to specific roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: CurrentUser = Depends(require_role(UserRole.admin))
        ):
            ...

    Multiple roles:
        @router.get("/partners-and-admins")
        async def endpoint(
            user: CurrentUser = Depends(require_role(UserRole.talent_partner, UserRole.admin))
        ):
            ...
    """
    async def role_checker(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {', '.join(r.value for r in allowed_roles)}",
            )
        return user

    return role_checker


# Convenience dependencies for common role combinations
require_admin = require_role(UserRole.admin)
require_talent_partner = require_role(UserRole.talent_partner, UserRole.admin)
require_client = require_role(UserRole.client, UserRole.admin)
require_any_authenticated = require_role(
    UserRole.talent_partner, UserRole.client, UserRole.admin
)
```

### Shared Dependencies (`backend/api/deps.py`)

```python
from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger("recruittech.deps")

# Supabase client singletons
_supabase_client: Client | None = None
_supabase_admin_client: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client with anon key (respects RLS)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
    return _supabase_client


def get_supabase_admin() -> Client:
    """Get Supabase client with service key (bypasses RLS).

    Use for system operations: ingestion, matching, signal tracking.
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        _supabase_admin_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
    return _supabase_admin_client
```

### Tests (`backend/tests/test_api.py`)

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Health endpoint returns 200 with correct payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "recruittech-api"
    assert "version" in data


def test_health_check_has_request_id():
    """Logging middleware adds X-Request-ID header."""
    response = client.get("/health")
    assert "x-request-id" in response.headers


def test_not_found():
    """Non-existent routes return structured 404."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404


def test_protected_endpoint_no_auth():
    """Protected endpoints return 403 without auth token.

    This test validates that the security middleware is wired up.
    Actual protected endpoints are tested in later tasks.
    """
    # Once candidate routes exist, this will be:
    # response = client.get("/api/candidates")
    # assert response.status_code == 403
    pass  # Placeholder until routes exist
```

## Outputs
- `backend/main.py`
- `backend/api/__init__.py`
- `backend/api/auth.py`
- `backend/api/deps.py`
- `backend/tests/test_api.py`

## Acceptance Criteria
1. `cd backend && uvicorn main:app --reload` starts without errors
2. `GET http://localhost:8000/health` returns `{"status": "healthy", ...}` with status 200
3. Response includes `X-Request-ID` header (logging middleware works)
4. `GET /docs` shows FastAPI Swagger UI
5. `python -m pytest tests/test_api.py -v` — all tests pass
6. `get_current_user` correctly decodes a valid Supabase JWT and returns `CurrentUser`
7. `require_role(UserRole.admin)` rejects non-admin tokens with 403

## Handoff Notes
- **To Task 04-08:** Import auth helpers as `from api.auth import get_current_user, require_role, CurrentUser`. Use `Depends(require_role(UserRole.talent_partner, UserRole.admin))` for role-gated endpoints.
- **To Task 04-08:** Import Supabase clients as `from api.deps import get_supabase_admin`. Use admin client for system operations (ingestion, matching), anon client for user-scoped queries.
- **To Agent B:** API base URL is `http://localhost:8000`. Health check at `GET /health`. All protected endpoints need `Authorization: Bearer <supabase_jwt>` header. Swagger docs at `GET /docs`.
- **Decision:** Router includes are commented out in `main.py`. Each task uncomments and adds its router as endpoints are built. This avoids import errors from non-existent modules.
- **Decision:** CORS allows `http://localhost:3000` (Next.js dev server). Configurable via `CORS_ORIGINS` env var.

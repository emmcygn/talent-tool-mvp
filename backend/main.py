from contextlib import asynccontextmanager
import logging
import time
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recruittech")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("RecruitTech API starting up")
    from adapters.registry import init_adapters
    init_adapters()
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

@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "path": request.url.path},
    )


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
@app.get("/api/health", tags=["system"], include_in_schema=False)
async def health_check():
    """Health check endpoint. Returns 200 if API is running."""
    return {
        "status": "healthy",
        "service": "recruittech-api",
        "version": "0.1.0",
    }



# ---- Users/Me ----

from api.auth import get_current_user as _get_current_user
from api.auth import CurrentUser as _CurrentUser


@app.get("/api/users/me", tags=["users"])
async def get_me(user: _CurrentUser = Depends(_get_current_user)):
    """Get the current authenticated user's profile."""
    try:
        from api.deps import get_supabase_admin
        supabase = get_supabase_admin()
        result = supabase.table("users").select("*").eq("id", str(user.id)).single().execute()
        if result.data:
            return result.data
    except Exception:
        pass
    # Fallback: return what we know from the JWT
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.email.split("@")[0].split(".")[0].title(),
        "last_name": "",
        "role": user.role.value,
        "organisation_id": None,
        "is_active": True,
    }


# ---- Router Includes ----

from api.candidates import router as candidates_router
from api.roles import router as roles_router
from api.matches import router as matches_router
from api.collections import router as collections_router
from api.handoffs import router as handoffs_router
from api.quotes import router as quotes_router
from api.copilot import router as copilot_router
from api.signals import router as signals_router
from api.admin import router as admin_router

app.include_router(candidates_router, prefix="/api/candidates", tags=["candidates"])
app.include_router(roles_router, prefix="/api/roles", tags=["roles"])
app.include_router(matches_router, prefix="/api/matches", tags=["matches"])
app.include_router(collections_router, prefix="/api/collections", tags=["collections"])
app.include_router(handoffs_router, prefix="/api/handoffs", tags=["handoffs"])
app.include_router(quotes_router, prefix="/api/quotes", tags=["quotes"])
app.include_router(copilot_router, prefix="/api/copilot", tags=["copilot"])
app.include_router(signals_router, prefix="/api/signals", tags=["signals"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import uvicorn

from backend.core.config import settings, startup_validation
from backend.core.logging_config import setup_logging
from backend.core.exceptions import MedSightException
from backend.core.middleware import (
    RequestIDMiddleware, SecurityHeadersMiddleware, AccessLogMiddleware, rate_limit_handler, limiter
)
from backend.db.session import init_db, engine
from slowapi.errors import RateLimitExceeded

# ═══ Router Imports ═══
from backend.api.v1.routers.auth import router as auth_router
from backend.api.v1.routers.users import router as users_router

# ML-dependent routers: import gracefully (they need torch, transformers, etc.)
_ml_routers_loaded = True
try:
    from backend.api.v1.routers.analyze import router as analyze_router
    from backend.api.v1.routers.chat import router as chat_router
    from backend.api.v1.routers.report import router as report_router
except (ImportError, OSError) as e:
    _ml_routers_loaded = False
    _ml_import_error = str(e)

# ML system imports (optional — graceful degradation)
_ml_system_loaded = True
try:
    from backend.ml.registry import ModelRegistry
    from backend.orchestration.queue import task_queue
    from backend.orchestration.scheduler import start_scheduler, stop_scheduler
except (ImportError, OSError) as e:
    _ml_system_loaded = False
    _ml_system_error = str(e)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────
    setup_logging()
    logger.info("🚀 MedSight AI starting up...")

    startup_validation()
    logger.info("✅ Configuration validated")

    await init_db()
    logger.info("✅ Database initialized")

    # Auto-download models from HuggingFace if not present locally
    try:
        from backend.ml.vision.hf_download import ensure_models
        ensure_models()
    except Exception as e:
        logger.warning(f"⚠️ HuggingFace model download skipped: {e}")

    # ML model registry - Load in background to prevent blocking the API
    if _ml_system_loaded:
        try:
            registry = ModelRegistry()
            app.state.model_registry = registry
            if _ml_system_loaded:
                task_queue._pipeline.registry = registry
            
            # Spawn background task for heavy loading
            async def load_models():
                if not settings.LOAD_ML_MODELS:
                    logger.info("⏩ Skipping ML models loading (LOAD_ML_MODELS=false)")
                    return
                try:
                    await registry.startup_load()
                    logger.info("✅ ML models background loading complete")
                except Exception as e:
                    logger.error(f"❌ ML background loading failed: {e}")
            
            import asyncio
            asyncio.create_task(load_models())
            logger.info("🚀 ML models loading initiated in background")
        except Exception as e:
            logger.warning(f"⚠️ ML registry initialization failed: {e}")
            app.state.model_registry = None
    else:
        logger.warning(f"⚠️ ML system not available: {_ml_system_error}")
        app.state.model_registry = None

    # Task queue
    if _ml_system_loaded:
        try:
            await task_queue.start()
            app.state.task_queue = task_queue
            logger.info("✅ Task queue started")
        except Exception as e:
            logger.warning(f"⚠️ Task queue failed to start: {e}")
    else:
        logger.warning("⚠️ Task queue not available (ML dependencies missing)")

    if _ml_system_loaded:
        try:
            start_scheduler()
            logger.info("✅ Scheduler started")
        except Exception as e:
            logger.warning(f"⚠️ Scheduler failed to start: {e}")

    app.state.start_time = datetime.now(timezone.utc)
    app.state.is_ready = True
    logger.info("🟢 MedSight AI ready to serve requests")

    yield  # ── APP RUNS HERE ──

    # ── SHUTDOWN ─────────────────────────────────────────
    logger.info("⏳ MedSight AI shutting down...")

    if _ml_system_loaded and hasattr(app.state, "task_queue"):
        try:
            await task_queue.stop()
        except Exception:
            pass
        try:
            stop_scheduler()
        except Exception:
            pass

    await engine.dispose()
    logger.info("✅ Graceful shutdown complete")


app = FastAPI(
    title="MedSight AI",
    description="Multimodal Medical Diagnostic Platform powered by deep learning",
    version=settings.VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "System health checks"},
        {"name": "Authentication", "description": "Login, registration, and tokens"},
        {"name": "Users", "description": "User profiles and session history"},
        {"name": "Analysis", "description": "Multimodal analysis endpoints"},
        {"name": "Chat", "description": "RAG-powered medical Q&A"},
        {"name": "Reports", "description": "PDF report generation"},
    ]
)

app.state.limiter = limiter

# ═══ MIDDLEWARE LAYER ═══
# SessionMiddleware is required by authlib for OAuth state management
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID", "Accept"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=86400,
)
app.add_middleware(AccessLogMiddleware)


# ═══ EXCEPTION HANDLERS ═══
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(map(str, err["loc"])), "message": err["msg"]} for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"error_code": "VALIDATION_ERROR", "details": errors}
    )

@app.exception_handler(MedSightException)
async def medsight_exception_handler(request: Request, exc: MedSightException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message, "request_id": getattr(request.state, "request_id", None)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred", "request_id": getattr(request.state, "request_id", None)}
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# ═══════════════════════════════════════════════════════════════════════
# ROUTE REGISTRATION
# ═══════════════════════════════════════════════════════════════════════

# Root
@app.get("/")
async def root():
    return {"name": "MedSight AI", "version": settings.VERSION, "status": "operational", "docs": "/docs"}

# Health (always inline — no heavy deps)
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for frontend status monitoring."""
    uptime = None
    if hasattr(app.state, "start_time"):
        uptime = (datetime.now(timezone.utc) - app.state.start_time).total_seconds()
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime,
        "ml_available": _ml_system_loaded and getattr(app.state, "model_registry", None) is not None,
    }

# Auth (real router — no ML deps)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# Users (real router — no ML deps)
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])

# ML-dependent routers: real if loaded, stubs if not
if _ml_routers_loaded:
    app.include_router(analyze_router, prefix="/api/v1/analyze", tags=["Analysis"])
    app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(report_router, prefix="/api/v1/report", tags=["Reports"])
    logger.info("✅ All ML routers registered")
else:
    # Fallback stubs for ML endpoints when dependencies are missing
    @app.post("/api/v1/analyze", tags=["Analysis"])
    async def analyze_fallback():
        return JSONResponse(status_code=503, content={
            "error_code": "ML_UNAVAILABLE",
            "message": f"ML pipeline not available: {_ml_import_error}"
        })

    @app.get("/api/v1/analyze/status/{task_id}", tags=["Analysis"])
    async def analyze_status_fallback(task_id: str):
        return JSONResponse(status_code=503, content={"error_code": "ML_UNAVAILABLE"})

    @app.get("/api/v1/analyze/result/{session_id}", tags=["Analysis"])
    async def analyze_result_fallback(session_id: str):
        return JSONResponse(status_code=503, content={"error_code": "ML_UNAVAILABLE"})

    @app.post("/api/v1/chat", tags=["Chat"])
    async def chat_fallback():
        return JSONResponse(status_code=503, content={"error_code": "ML_UNAVAILABLE"})

    @app.get("/api/v1/report/{session_id}", tags=["Reports"])
    async def report_fallback(session_id: str):
        return JSONResponse(status_code=503, content={"error_code": "ML_UNAVAILABLE"})


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,
        access_log=False
    )

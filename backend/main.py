from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, UTC
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

# Stubs for components loaded during lifespan (to be implemented in Orchestration & ML)
# from backend.ml.registry import model_registry
# from backend.orchestration.queue import task_queue
# from backend.orchestration.scheduler import scheduler

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
    
    # await model_registry.startup_load()
    logger.info("✅ ML models loaded (stubbed)")
    
    # await task_queue.start()
    logger.info("✅ Task queue started (stubbed)")
    
    # scheduler.start()
    logger.info("✅ Scheduler started (stubbed)")
    
    app.state.start_time = datetime.now(UTC)
    logger.info("🟢 MedSight AI ready to serve requests")
    
    yield  # ── APP RUNS HERE ──
    
    # ── SHUTDOWN ─────────────────────────────────────────
    logger.info("⏳ MedSight AI shutting down...")
    
    # await task_queue.stop()
    # scheduler.shutdown(wait=False)
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
        {"name": "Analysis", "description": "Multimodal analysis endpoints"},
    ]
)

app.state.limiter = limiter

# MIDDLEWARE LAYER
# 1. TrustedHost limits allowed host headers
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.render.com"])
# 2. RequestID assigns correlation ID early
app.add_middleware(RequestIDMiddleware)
# 3. SecurityHeaders applies CSP, XSS, etc.
app.add_middleware(SecurityHeadersMiddleware)
# 4. CORS must be before rate limiting/auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID", "Accept"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=86400,
)
# 5. AccessLog tracks the HTTP request details
app.add_middleware(AccessLogMiddleware)

# Exception Handlers
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

# ROUTERS (Stubs until created)
# app.include_router(health_router, prefix="/api/v1", tags=["Health"])
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(analyze_router, prefix="/api/v1/analyze", tags=["Analysis"])

@app.get("/")
async def root():
    return {"name": "MedSight AI", "version": settings.VERSION, "status": "operational", "docs": "/docs"}

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,
        access_log=False
    )

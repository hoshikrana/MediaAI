import uuid
import time
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from backend.core.config import settings
from backend.core.logging_config import _request_id_var

logger = logging.getLogger("access")

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.is_production:
            # Check if request came in as HTTP (Render.com forwards as HTTPS but sets X-Forwarded-Proto)
            proto = request.headers.get("X-Forwarded-Proto", "https")
            if proto == "http":
                https_url = str(request.url).replace("http://", "https://", 1)
                return RedirectResponse(https_url, status_code=301)
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Always add these headers:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), "
            "payment=(), usb=(), magnetometer=()"
        ) # microphone=(self) required for Whisper voice input
        
        # Production only:
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        
        # Remove headers that leak server info:
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        return response

def get_rate_limit_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"
    return f"ip:{request.client.host}"

limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["1000/minute"],
    storage_uri="memory://"
)

async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    retry_after = exc.retry_after if hasattr(exc, "retry_after") else 60
    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. Try again in {retry_after} seconds.",
            "retry_after_seconds": retry_after,
            "limit": str(exc.limit)
        },
        headers={"Retry-After": str(retry_after)}
    )

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        _request_id_var.set(request_id)
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.monotonic()
        response = await call_next(request)
        duration = int((time.monotonic() - start_time) * 1000)
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration}ms)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        return response

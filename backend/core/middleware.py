from fastapi import Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from backend.core.config import settings

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
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
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

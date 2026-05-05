from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

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

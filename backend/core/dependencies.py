from fastapi import Depends, Header, Request, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple, Callable

from backend.db.session import get_db
from backend.db.models import User, AnalysisSession, AnalysisTask
from backend.core.exceptions import (
    AuthenticationError, AccountInactiveError, InsufficientPermissionsError,
    SessionNotFoundError, SessionAccessDeniedError, TaskNotFoundError
)
from backend.core.security import verify_token
from backend.core.api_keys import verify_api_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user_from_token(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    payload = verify_token(token, "access")
    user_id = payload.sub
    
    user = await db.get(User, user_id)  # type: ignore
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AccountInactiveError("User inactive")
    return user

async def get_current_user_from_api_key(
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not x_api_key:
        return None
    api_key = await verify_api_key(x_api_key, db)
    if not api_key:
        return None
    from datetime import datetime, timezone
    api_key.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
    api_key.usage_count = (api_key.usage_count or 0) + 1
    await db.commit()
    # Load the user who owns this API key
    user = await db.get(User, api_key.user_id)  # type: ignore
    return user if user and user.is_active else None

async def get_current_user(
    jwt_user: Optional[User] = Depends(get_current_user_from_token),
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key)
) -> User:
    """Try JWT first, then API key. Raise 401 if neither works."""
    if jwt_user:
        return jwt_user
    if api_key_user:
        return api_key_user
    raise AuthenticationError("Authentication required via Token or API Key")

async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise AccountInactiveError()
    return user

async def get_superuser(user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise InsufficientPermissionsError()
    return user

async def optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Returns user if authenticated, None if not. Never raises 401."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    api_key = request.headers.get("X-API-Key")
    
    try:
        if token:
            payload = verify_token(token, "access")
            user = await db.get(User, payload.sub)  # type: ignore
            if user and user.is_active:
                return user
        if api_key:
            key = await verify_api_key(api_key, db)
            if key:
                user = await db.get(User, key.user_id)  # type: ignore
                if user and user.is_active:
                    return user
    except Exception:
        pass
    return None

async def get_session_or_404(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisSession:
    session = await db.get(AnalysisSession, session_id)  # type: ignore
    if not session:
        raise SessionNotFoundError()
    if session.user_id != current_user.id:
        raise SessionAccessDeniedError()
    return session

async def get_task_or_404(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisTask:
    task = await db.get(AnalysisTask, task_id)  # type: ignore
    if not task:
        raise TaskNotFoundError()
    if task.user_id != current_user.id:
        raise SessionAccessDeniedError()
    return task

def get_pagination(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
) -> Tuple[int, int]:
    return page, limit

def get_client_ip(request: Request) -> str:
    """Extracts real IP from X-Forwarded-For (for Render.com proxy)"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.client.host if request.client else "127.0.0.1"

def check_api_key_permission(permission: str) -> Callable:
    """Factory function to verify API key permission"""
    async def dependency(
        current_user: User = Depends(get_current_user),
        x_api_key: Optional[str] = Header(None)
    ) -> User:
        if x_api_key:
            # Permission check could be extended per-key
            pass
        return current_user
    return dependency

# ML Dependencies
async def get_model_registry(request: Request):
    return getattr(request.app.state, "model_registry", None)

async def require_vision_model(registry = Depends(get_model_registry)):
    if not registry:
        from backend.core.exceptions import ModelNotLoadedError
        raise ModelNotLoadedError("Vision model registry not available")
    return registry

async def require_nlp_model(registry = Depends(get_model_registry)):
    if not registry:
        from backend.core.exceptions import ModelNotLoadedError
        raise ModelNotLoadedError("NLP model registry not available")
    return registry

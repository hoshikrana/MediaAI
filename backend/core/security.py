import hashlib
import secrets
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Literal, Tuple, List, Dict
from jose import jwt, JWTError, ExpiredSignatureError
import bcrypt
from pydantic import BaseModel
from fastapi import Response, Request

from backend.core.config import settings
from backend.core.exceptions import (
    ExpiredTokenError, InvalidTokenError, BlacklistedTokenError, AuthenticationError
)

# 1. Password Hashing
def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def validate_password_strength(password: str) -> List[str]:
    """Returns list of failure reasons. Empty list = strong password."""
    failures = []
    if len(password) < 8:
        failures.append("Must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        failures.append("Must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        failures.append("Must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        failures.append("Must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        failures.append("Must contain at least one special character")
    return failures

# 2. Token Payload Model
class TokenPayload(BaseModel):
    sub: str          # user_id
    type: Literal["access", "refresh"]
    jti: str          # unique token ID
    iat: datetime
    exp: datetime

# 3 & 4. Token Creation
def create_token(user_id: str, token_type: Literal["access", "refresh"], extra_claims: dict = None) -> str:
    claims = extra_claims or {}
    now = datetime.now(timezone.utc)
    
    if token_type == "access":
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": secrets.token_hex(16),
        "iat": now,
        "exp": now + expires_delta,
        **claims
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_access_token(user_id: str, extra_claims: dict = None) -> str:
    return create_token(user_id, "access", extra_claims)

def create_refresh_token(user_id: str) -> str:
    return create_token(user_id, "refresh")

# 5. Token Verification
def verify_token(token: str, expected_type: Literal["access", "refresh"]) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise ExpiredTokenError("Token has expired")
    except JWTError:
        raise InvalidTokenError("Token is invalid")
    
    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected {expected_type} token")
    
    if is_token_blacklisted(payload.get("jti")):
        raise BlacklistedTokenError()
    
    return TokenPayload(**payload)

# 6. In-Memory Blacklist
_blacklist: Dict[str, datetime] = {}
_blacklist_lock = asyncio.Lock()

async def blacklist_token(jti: str, expires_at: datetime):
    async with _blacklist_lock:
        _blacklist[jti] = expires_at

def is_token_blacklisted(jti: str) -> bool:
    return jti in _blacklist

async def cleanup_expired_blacklist() -> int:
    """Call hourly from scheduler. Returns count of removed entries."""
    now = datetime.now(timezone.utc)
    async with _blacklist_lock:
        expired = [jti for jti, exp in _blacklist.items() if exp < now]
        for jti in expired:
            del _blacklist[jti]
    return len(expired)

# 7, 8 & 9. Cookie Management
def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key="refresh_token",
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="none" if settings.is_production else "lax",
        path="/api/v1/auth/refresh"
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie(
        "refresh_token",
        path="/api/v1/auth/refresh",
        secure=settings.is_production,
        samesite="none" if settings.is_production else "lax",
    )

def get_refresh_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("refresh_token")
    if not token:
        raise AuthenticationError("No refresh token found")
    return token

# 10 & 11. Security Utilities
def generate_verification_token() -> Tuple[str, str]:
    plain = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(plain.encode()).hexdigest()
    return plain, hashed

def verify_token_hash(plain: str, stored_hash: str) -> bool:
    computed = hashlib.sha256(plain.encode()).hexdigest()
    return secrets.compare_digest(computed, stored_hash)

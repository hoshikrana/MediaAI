import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import APIKey

def generate_api_key() -> tuple[str, str]:
    """Returns (plain_key, hashed_key)"""
    prefix = "ms_live"
    random_part = secrets.token_hex(32)
    plain_key = f"{prefix}_{random_part}"
    hashed = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, hashed

def hash_api_key(plain_key: str) -> str:
    return hashlib.sha256(plain_key.encode()).hexdigest()

async def verify_api_key(plain_key: str, db: AsyncSession) -> APIKey | None:
    hashed = hash_api_key(plain_key)
    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == hashed, APIKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        return None
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return None
        
    return api_key

class APIKeyRateLimiter:
    """In-memory rate limiter for API Keys."""
    def __init__(self):
        self._counters: dict[str, dict] = {}
        
    async def check_and_increment(self, key_id: str, limit: int) -> bool:
        current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
        
        if key_id not in self._counters or self._counters[key_id]["hour"] != current_hour:
            self._counters[key_id] = {"hour": current_hour, "count": 0}
            
        if self._counters[key_id]["count"] >= limit:
            return False
            
        self._counters[key_id]["count"] += 1
        return True
        
    def get_remaining(self, key_id: str, limit: int) -> int:
        current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
        if key_id not in self._counters or self._counters[key_id]["hour"] != current_hour:
            return limit
        return max(0, limit - self._counters[key_id]["count"])

api_key_limiter = APIKeyRateLimiter()

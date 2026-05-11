import asyncio
import logging
from datetime import datetime, timedelta, timezone
from backend.core.exceptions import AccountLockedError

logger = logging.getLogger(__name__)

class BruteForceProtector:
    """In-memory brute force protection for login attempts"""
    
    THRESHOLDS = [
        (3, 30),    # 3 failures -> 30 second lockout
        (5, 300),   # 5 failures -> 5 minute lockout
        (10, 3600), # 10 failures -> 1 hour lockout
    ]
    
    def __init__(self):
        self._attempts: dict[str, list[datetime]] = {}
        self._lockouts: dict[str, datetime] = {}
        
    async def check_and_record_failure(self, ip: str):
        now = datetime.now(timezone.utc)

        self.check_lockout(ip, now)
            
        if ip not in self._attempts:
            self._attempts[ip] = []
            
        # Clean old attempts
        self._attempts[ip] = [t for t in self._attempts[ip] if (now - t).seconds < 3600]
        self._attempts[ip].append(now)
        
        count = len(self._attempts[ip])
        for threshold, lockout_seconds in reversed(self.THRESHOLDS):
            if count >= threshold:
                self._lockouts[ip] = now + timedelta(seconds=lockout_seconds)
                logger.warning(f"Login lockout: {ip}, attempts: {count}, lockout: {lockout_seconds}s")
                raise AccountLockedError(f"Account locked for {lockout_seconds}s")

    def check_lockout(self, ip: str, now: datetime | None = None):
        now = now or datetime.now(timezone.utc)
        if ip in self._lockouts and self._lockouts[ip] > now:
            remaining = int((self._lockouts[ip] - now).total_seconds())
            raise AccountLockedError(f"Too many failed attempts. Try in {remaining}s")
                
    def record_success(self, ip: str):
        self._attempts.pop(ip, None)
        self._lockouts.pop(ip, None)
        
    def is_locked(self, ip: str) -> bool:
        return ip in self._lockouts and self._lockouts[ip] > datetime.now(timezone.utc)
        
    async def cleanup(self):
        now = datetime.now(timezone.utc)
        expired = [ip for ip, until in self._lockouts.items() if until < now]
        for ip in expired:
            del self._lockouts[ip]
            self._attempts.pop(ip, None)

brute_force_protector = BruteForceProtector()

import asyncio
import random
import logging
from enum import Enum
from functools import wraps
from typing import Callable, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.core.exceptions import (
    InferenceError, CircuitOpenError, ValidationError, 
    SecurityError, ModelNotLoadedError
)

logger = logging.getLogger(__name__)

# ━━━ PART A: RETRY DECORATOR ━━━

@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    exponential_base: float = 2.0
    max_delay_seconds: float = 30.0
    jitter_factor: float = 0.2
    retry_on: Tuple[type[Exception], ...] = (InferenceError, TimeoutError, asyncio.TimeoutError)
    no_retry_on: Tuple[type[Exception], ...] = (ValidationError, SecurityError, ModelNotLoadedError)

def retry(config: RetryConfig | None = None):
    """Decorator factory for async functions to retry on failure with exponential backoff and jitter."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                
                except config.no_retry_on as e:
                    # Immediately fail on exceptions we know won't succeed on retry
                    raise
                
                except config.retry_on as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(f"{func.__name__} failed after {attempt} attempts: {e}")
                        raise
                    
                    delay = min(
                        config.initial_delay_seconds * (config.exponential_base ** (attempt - 1)),
                        config.max_delay_seconds
                    )
                    jitter = delay * config.jitter_factor * (2 * random.random() - 1)
                    actual_delay = max(0.1, delay + jitter)
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{config.max_attempts} failed. "
                        f"Retrying in {actual_delay:.1f}s. Error: {e}"
                    )
                    await asyncio.sleep(actual_delay)
            
            if last_exception:
                raise last_exception
        return wrapper
    return decorator

# ━━━ PART B: CIRCUIT BREAKER ━━━

class CircuitState(Enum):
    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"            # Failing — reject all calls
    HALF_OPEN = "HALF_OPEN"  # Testing — allow one call

@dataclass
class CircuitBreakerConfig:
    name: str
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    call_timeout_seconds: float = 30.0

class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
            if elapsed >= self.config.timeout_seconds:
                return CircuitState.HALF_OPEN
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            current_state = self.state
            
            if current_state == CircuitState.OPEN:
                next_attempt_in = (
                    self.config.timeout_seconds -
                    (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
                )
                raise CircuitOpenError(
                    f"Circuit '{self.config.name}' is OPEN. Retry in {max(0, next_attempt_in):.0f}s"
                )
        
        try:
            # Enforce timeout at the circuit breaker level
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.call_timeout_seconds
            )
            await self._on_success()
            return result
            
        except CircuitOpenError:
            raise
        except Exception as e:
            await self._on_failure()
            raise
            
    async def _on_success(self):
        async with self._lock:
            current_state = self.state
            if current_state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit '{self.config.name}' CLOSED (recovered)")
            elif current_state == CircuitState.CLOSED:
                self._failure_count = 0
                
    async def _on_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._success_count = 0
            self._last_failure_time = datetime.now(timezone.utc)
            
            current_state = self.state
            if current_state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit '{self.config.name}' re-OPENED (test failed)")
            elif current_state == CircuitState.CLOSED and self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(f"Circuit '{self.config.name}' OPENED after {self._failure_count} failures")
                
    def force_close(self):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        logger.info(f"Circuit '{self.config.name}' force-closed by admin")

    def get_status(self) -> dict:
        return {
            "name": self.config.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.config.failure_threshold,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "next_attempt_seconds": max(0, self.config.timeout_seconds - (
                (datetime.now(timezone.utc) - self._last_failure_time).total_seconds()
            )) if self._state == CircuitState.OPEN and self._last_failure_time else None
        }

CIRCUIT_BREAKERS = {
    "vision": CircuitBreaker(CircuitBreakerConfig("vision", failure_threshold=3, timeout_seconds=60, call_timeout_seconds=45)),
    "nlp": CircuitBreaker(CircuitBreakerConfig("nlp", failure_threshold=5, timeout_seconds=30, call_timeout_seconds=20)),
    "fusion": CircuitBreaker(CircuitBreakerConfig("fusion", failure_threshold=3, timeout_seconds=45, call_timeout_seconds=30)),
    "rag": CircuitBreaker(CircuitBreakerConfig("rag", failure_threshold=5, timeout_seconds=60, call_timeout_seconds=30)),
}

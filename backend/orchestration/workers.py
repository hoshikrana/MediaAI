"""
Worker pool management for analysis pipeline execution.
The TaskQueue in queue.py handles dispatch; this module provides
worker health monitoring and concurrency control.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WorkerStats:
    """Tracks per-worker execution statistics."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_duration_ms: float = 0.0
    last_active: Optional[datetime] = None


@dataclass
class WorkerPool:
    """
    Manages a pool of async worker slots for analysis tasks.
    Works alongside the TaskQueue — the queue dispatches, workers execute.
    """
    max_workers: int = 2
    _active_count: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _stats: WorkerStats = field(default_factory=WorkerStats)

    async def acquire(self) -> bool:
        """Try to acquire a worker slot. Returns False if pool is full."""
        async with self._lock:
            if self._active_count >= self.max_workers:
                return False
            self._active_count += 1
            return True

    async def release(self, success: bool = True, duration_ms: float = 0.0):
        """Release a worker slot after task completion."""
        async with self._lock:
            self._active_count = max(0, self._active_count - 1)
            self._stats.total_tasks += 1
            self._stats.last_active = datetime.now(timezone.utc)
            if success:
                self._stats.completed_tasks += 1
            else:
                self._stats.failed_tasks += 1
            # Running average
            if self._stats.total_tasks > 0:
                alpha = 1.0 / self._stats.total_tasks
                self._stats.avg_duration_ms = (
                    (1 - alpha) * self._stats.avg_duration_ms + alpha * duration_ms
                )

    @property
    def available_slots(self) -> int:
        return max(0, self.max_workers - self._active_count)

    @property
    def is_full(self) -> bool:
        return self._active_count >= self.max_workers

    def get_status(self) -> dict:
        return {
            "max_workers": self.max_workers,
            "active": self._active_count,
            "available": self.available_slots,
            "total_processed": self._stats.total_tasks,
            "completed": self._stats.completed_tasks,
            "failed": self._stats.failed_tasks,
            "avg_duration_ms": round(self._stats.avg_duration_ms, 1),
        }


# Singleton pool
worker_pool = WorkerPool(max_workers=2)

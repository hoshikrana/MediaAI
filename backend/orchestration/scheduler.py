"""
Background scheduler for periodic maintenance tasks.
Uses APScheduler for in-process cron-like scheduling.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def cleanup_expired_tokens():
    """Remove expired JWTs from the in-memory blacklist."""
    from backend.core.security import cleanup_expired_blacklist
    removed = await cleanup_expired_blacklist()
    if removed:
        logger.debug(f"Cleaned up {removed} expired blacklisted tokens")


async def aggregate_daily_stats():
    """Placeholder: aggregate usage stats into daily summaries."""
    logger.debug("Daily stats aggregation triggered (no-op until stats table populated)")


async def cleanup_expired_sessions():
    """Delete expired analysis sessions and related task/chat rows via cascades."""
    from datetime import datetime, timezone
    from sqlalchemy import delete
    from backend.db.models import AnalysisSession
    from backend.db.session import AsyncSessionLocal

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with AsyncSessionLocal() as db:
        result = await db.execute(delete(AnalysisSession).where(AnalysisSession.expires_at < now))
        await db.commit()
    removed = result.rowcount or 0
    if removed:
        logger.info(f"Cleaned up {removed} expired analysis sessions")


async def cleanup_temp_files():
    """Remove stale files from the temp upload directory."""
    import os
    from pathlib import Path
    from datetime import datetime, timezone, timedelta
    
    temp_dir = Path("./backend/temp")
    if not temp_dir.exists():
        return
    
    cutoff = datetime.now(timezone.utc).timestamp() - 3600  # 1 hour old
    removed = 0
    for f in temp_dir.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    if removed:
        logger.info(f"Cleaned up {removed} stale temp files")


def start_scheduler():
    """Register all periodic jobs and start the scheduler."""
    scheduler.add_job(
        cleanup_expired_tokens,
        trigger=IntervalTrigger(hours=1),
        id="cleanup_tokens",
        name="Cleanup expired token blacklist",
        replace_existing=True
    )
    scheduler.add_job(
        cleanup_temp_files,
        trigger=IntervalTrigger(minutes=30),
        id="cleanup_temp",
        name="Cleanup stale temp files",
        replace_existing=True
    )
    scheduler.add_job(
        cleanup_expired_sessions,
        trigger=IntervalTrigger(hours=6),
        id="cleanup_sessions",
        name="Cleanup expired analysis sessions",
        replace_existing=True
    )
    scheduler.add_job(
        aggregate_daily_stats,
        trigger=IntervalTrigger(hours=24),
        id="daily_stats",
        name="Aggregate daily statistics",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started with {len(scheduler.get_jobs())} jobs")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")

import asyncio
import uuid
import logging
from pathlib import Path
from datetime import datetime, UTC
from sqlalchemy import select, func

from backend.db.models import AnalysisTask, AnalysisSession
from backend.core.exceptions import TaskNotFoundError, SessionAccessDeniedError
from backend.core.logging_config import ml_logger

logger = logging.getLogger(__name__)

class AnalysisTaskQueue:
    MAX_CONCURRENT = 2
    WORKER_SLEEP_SECONDS = 5
    
    def __init__(self, db_session_factory, pipeline):
        self._db_factory = db_session_factory
        self._pipeline = pipeline
        self._new_task_event = asyncio.Event()
        self._active_count = 0
        self._active_lock = asyncio.Lock()
        self._worker_task: asyncio.Task | None = None
        self._is_running = False
    
    async def start(self):
        self._is_running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Task queue worker started")
    
    async def stop(self):
        logger.info("Task queue stopping...")
        self._is_running = False
        self._new_task_event.set()
        
        deadline = asyncio.get_event_loop().time() + 60
        while self._active_count > 0:
            if asyncio.get_event_loop().time() > deadline:
                logger.warning(f"Shutdown timeout: {self._active_count} tasks still running")
                break
            await asyncio.sleep(1)
        
        if self._worker_task:
            self._worker_task.cancel()

    async def submit(self, session_id: str, user_id: str | None, image_path: str, symptoms_text: str, priority: int = 1) -> str:
        task_id = str(uuid.uuid4())
        async with self._db_factory() as db:
            task = AnalysisTask(
                id=task_id, session_id=session_id, user_id=user_id,
                status="PENDING", priority=priority,
                image_path=image_path, symptoms_text=symptoms_text
            )
            db.add(task)
            await db.commit()
            
        self._new_task_event.set()
        return task_id

    async def get_status(self, task_id: str) -> dict:
        async with self._db_factory() as db:
            task = await db.get(AnalysisTask, task_id)
            if not task:
                raise TaskNotFoundError()
                
            position = None
            if task.status == "PENDING":
                result = await db.execute(
                    select(func.count(AnalysisTask.id)).where(
                        AnalysisTask.status == "PENDING",
                        AnalysisTask.priority >= task.priority,
                        AnalysisTask.created_at < task.created_at
                    )
                )
                position = result.scalar_one() + 1
                
            estimated_wait = None
            if position:
                slots_until_ours = max(0, position - self.MAX_CONCURRENT)
                estimated_wait = slots_until_ours * 45
                
            return {
                "task_id": task_id, "session_id": task.session_id, "status": task.status,
                "position_in_queue": position, "estimated_wait_seconds": estimated_wait,
                "started_at": task.started_at, "completed_at": task.completed_at,
                "error_message": task.error_message
            }

    async def cancel(self, task_id: str, user_id: str) -> bool:
        async with self._db_factory() as db:
            task = await db.get(AnalysisTask, task_id)
            if not task:
                raise TaskNotFoundError()
            if task.user_id != user_id:
                raise SessionAccessDeniedError()
            if task.status != "PENDING":
                return False
                
            task.status = "CANCELLED"
            image_path = Path(task.image_path)
            if image_path.exists():
                image_path.unlink()
                
            await db.commit()
            return True

    async def _worker_loop(self):
        logger.info("Worker loop started")
        while self._is_running:
            try:
                await asyncio.wait_for(
                    asyncio.shield(self._new_task_event.wait()), timeout=self.WORKER_SLEEP_SECONDS
                )
                self._new_task_event.clear()
            except asyncio.TimeoutError:
                pass
                
            if not self._is_running:
                break
                
            while self._active_count < self.MAX_CONCURRENT:
                task = await self._fetch_next_task()
                if not task:
                    break
                asyncio.create_task(self._process_task(task))
                
        logger.info("Worker loop stopped")

    async def _fetch_next_task(self) -> AnalysisTask | None:
        async with self._db_factory() as db:
            result = await db.execute(
                select(AnalysisTask).where(AnalysisTask.status == "PENDING")
                .order_by(AnalysisTask.priority.desc(), AnalysisTask.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            return result.scalar_one_or_none()

    async def _process_task(self, task: AnalysisTask):
        async with self._active_lock:
            self._active_count += 1
            
        try:
            async with self._db_factory() as db:
                task.status = "PROCESSING"
                task.started_at = datetime.now(UTC)
                await db.merge(task)
                await db.commit()
                
            result = await self._pipeline.run(
                session_id=task.session_id,
                image_path=Path(task.image_path),
                symptoms_text=task.symptoms_text or ""
            )
            
            async with self._db_factory() as db:
                db_task = await db.get(AnalysisTask, task.id)
                db_task.status = "COMPLETED"
                db_task.completed_at = datetime.now(UTC)
                
                session = await db.get(AnalysisSession, task.session_id)
                session.result_json = result.model_dump()
                session.status = "READY"
                session.risk_level = result.vision.risk_level if result.vision else "UNKNOWN"
                
                await db.commit()
                
            ml_logger.log_pipeline_step(
                "full_pipeline", "COMPLETED", 
                int((datetime.now(UTC) - task.started_at).total_seconds() * 1000), task.session_id
            )
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)
            async with self._db_factory() as db:
                db_task = await db.get(AnalysisTask, task.id)
                db_task.attempt_count = (db_task.attempt_count or 0) + 1
                
                if db_task.attempt_count < 3:
                    db_task.status = "PENDING"
                    self._new_task_event.set()
                else:
                    db_task.status = "FAILED"
                    db_task.error_message = str(e)[:500]
                    session = await db.get(AnalysisSession, task.session_id)
                    session.status = "FAILED"
                    session.error_message = "Analysis failed after 3 attempts"
                await db.commit()
                
        finally:
            try:
                Path(task.image_path).unlink(missing_ok=True)
            except Exception:
                pass
            async with self._active_lock:
                self._active_count -= 1
            self._new_task_event.set()

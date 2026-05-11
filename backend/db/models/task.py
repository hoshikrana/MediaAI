from sqlalchemy import String, Integer, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from backend.db.base import Base, UUIDMixin, TimestampMixin

class AnalysisTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_tasks"

    session_id: Mapped[str] = mapped_column(ForeignKey("analysis_sessions.id", ondelete="CASCADE"), unique=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED", name="task_status"), default="PENDING")
    priority: Mapped[int] = mapped_column(Integer, default=1, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    image_path: Mapped[str] = mapped_column(String(512))
    symptoms_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    session: Mapped["AnalysisSession"] = relationship(back_populates="task")

    __table_args__ = (
        Index('ix_task_queue', 'status', 'priority', 'created_at'),
    )

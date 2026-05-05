from sqlalchemy import Date, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from typing import Optional
from backend.db.base import Base, UUIDMixin, TimestampMixin

class DailyStats(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "daily_stats"

    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    total_analyses: Mapped[int] = mapped_column(Integer, default=0)
    completed_analyses: Mapped[int] = mapped_column(Integer, default=0)
    failed_analyses: Mapped[int] = mapped_column(Integer, default=0)
    avg_processing_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high_risk_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_risk_count: Mapped[int] = mapped_column(Integer, default=0)
    low_risk_count: Mapped[int] = mapped_column(Integer, default=0)
    vision_failures: Mapped[int] = mapped_column(Integer, default=0)
    nlp_failures: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)

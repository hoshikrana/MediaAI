from sqlalchemy import String, Enum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
from backend.db.base import Base, UUIDMixin, TimestampMixin

class AnalysisSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_sessions"

    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    patient_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(Enum("PENDING", "ANALYZING", "READY", "FAILED", "EXPIRED", name="session_status"), index=True, default="PENDING")
    image_filename: Mapped[str] = mapped_column(String(255))
    image_hash: Mapped[str] = mapped_column(String(64), index=True)
    symptoms_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(Enum("LOW", "MEDIUM", "HIGH", "UNKNOWN", name="risk_level"), index=True, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="sessions")
    task: Mapped[Optional["AnalysisTask"]] = relationship(back_populates="session", uselist=False, cascade="all, delete-orphan")
    chat_messages: Mapped[List["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    session_id: Mapped[str] = mapped_column(ForeignKey("analysis_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(Enum("user", "assistant", name="chat_role"))
    content: Mapped[str] = mapped_column(String)
    sources_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    token_count: Mapped[int] = mapped_column(default=0)

    session: Mapped["AnalysisSession"] = relationship(back_populates="chat_messages")

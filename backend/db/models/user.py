from sqlalchemy import Boolean, String, Integer, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from backend.db.base import Base, UUIDMixin, TimestampMixin

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Stored as ISO string or DateTime
    login_count: Mapped[int] = mapped_column(Integer, default=0)

    sessions: Mapped[List["AnalysisSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[List["APIKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @classmethod
    async def get_by_email(cls, db, email: str) -> Optional["User"]:
        result = await db.execute(select(cls).where(cls.email == email))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_google_id(cls, db, google_id: str) -> Optional["User"]:
        result = await db.execute(select(cls).where(cls.google_id == google_id))
        return result.scalar_one_or_none()

    def to_dict(self) -> dict:
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        d.pop("hashed_password", None)
        return d

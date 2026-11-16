from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class RepoStar(Base):
    __tablename__ = "repo_stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    delivery_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sender_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    sender_username: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stargazers_count: Mapped[int] = mapped_column(Integer, nullable=False)
    starred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

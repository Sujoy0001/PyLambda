from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UUID, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    username: Mapped[str] = mapped_column(String(150), index=True)
    useremail: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    isAdmin: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PhoneDetail(Base):
    __tablename__ = "phone_details"

    # Primary key for this details table
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 🔗 Foreign Key linking back to your existing User table
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True,  # Ensures a 1-to-1 relationship (one profile per user)
        nullable=False
    )
    
    # Data fields extracted straight from your verification API response
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, index=True) # international_format
    local_format: Mapped[str] = mapped_column(String(20))
    country_code: Mapped[str] = mapped_column(String(5))  # e.g., "IN"
    country_name: Mapped[str] = mapped_column(String(100)) # e.g., "India"
    location: Mapped[str] = mapped_column(String(150))     # e.g., "West Bengal"
    carrier: Mapped[str] = mapped_column(String(150))      # e.g., "Reliance Jio"
    line_type: Mapped[str] = mapped_column(String(20))     # e.g., "mobile"
    
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=text("now()")
    )

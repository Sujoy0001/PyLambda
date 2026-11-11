from sqlalchemy import UUID, String, Boolean, Float
from sqlalchemy.orm import mapped_column, Mapped
import uuid

from app.db.base import Base

class Products(Base):
    
    __tablename__ = "products"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(250), index=True)
    product_price: Mapped[float] = mapped_column(Float, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
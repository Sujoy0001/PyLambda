import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.products import Products
from app.schemas.products import ProductCreate

def get_product_by_id(db: Session, product_id: uuid.UUID) -> Products | None:
    return db.get(Products, product_id)


def get_products(db: Session, skip: int = 0, limit: int = 20) -> list[Products]:
    stmt = select(Products).order_by(Products.product_name).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def create_product(db: Session, data: ProductCreate) -> Products:
    product = Products(id=uuid.uuid4(), **data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
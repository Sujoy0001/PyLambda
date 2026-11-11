import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db          # adjust to your session dependency
from app.schemas.products import ProductRead
from app.services import product_service

router = APIRouter(prefix="/v1/products", tags=["products v1 (db)"])


@router.get("", response_model=list[ProductRead])
def list_products(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return product_service.get_products(db, skip, limit)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = product_service.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product
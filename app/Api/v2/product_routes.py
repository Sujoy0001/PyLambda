import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.redis import product_cache as cache
from app.db.session import get_db
from app.schemas.products import ProductCreate, ProductRead
from app.services import product_service

router = APIRouter(prefix="/v2/products", tags=["products v2 (redis)"])


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    r = request.app.state.redis
    key = cache.product_key(product_id)

    cached = await cache.get_cached(r, key)
    if cached:
        return cached                                   # cache hit

    product = await run_in_threadpool(product_service.get_product_by_id, db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    data = ProductRead.model_validate(product).model_dump(mode="json")
    await cache.set_cached(r, key, data, cache.PRODUCT_TTL)
    return data


@router.get("", response_model=list[ProductRead])
async def list_products(request: Request, skip: int = 0, limit: int = 20,
                        db: Session = Depends(get_db)):
    r = request.app.state.redis
    key = cache.list_key(skip, limit)

    cached = await cache.get_cached(r, key)
    if cached is not None:
        return cached

    products = await run_in_threadpool(product_service.get_products, db, skip, limit)
    data = [ProductRead.model_validate(p).model_dump(mode="json") for p in products]
    await cache.set_cached(r, key, data, cache.LIST_TTL)
    return data


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(body: ProductCreate, request: Request, db: Session = Depends(get_db)):
    product = await run_in_threadpool(product_service.create_product, db, body)
    await cache.invalidate_product(request.app.state.redis)   # clear stale lists
    return product
from fastapi import APIRouter

from app.Api.v1.auth_routes import router as auth_router_v1
from app.Api.v1.product_routes import router as products_router_v1


from app.Api.v2.product_routes import router as products_router_v2

api_router = APIRouter(prefix="/apps")

api_router.include_router(auth_router_v1)
api_router.include_router(products_router_v1)


api_router.include_router(products_router_v2)
from fastapi import APIRouter

from app.Auth.router import router as auth_route

router = APIRouter(prefix="/v1", tags=["V1 routes"])

router.include_router(auth_route, prefix="/auth", tags=["Authentication"])
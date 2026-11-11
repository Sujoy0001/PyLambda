from fastapi import APIRouter

from app.Auth.router import router as auth_router

router = APIRouter(prefix="/v1")

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

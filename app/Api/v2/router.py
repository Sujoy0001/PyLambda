from fastapi import APIRouter
from app.Api.v2.webhook import router as webhook_route

router = APIRouter(prefix="/v2", tags=["V2 routes"])

router.include_router(webhook_route)
from app.Api.V1.dataValue import router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(router, prefix='/v1', tags=["V1 router"])


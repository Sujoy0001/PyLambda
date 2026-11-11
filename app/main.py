# main.py
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.middlewares.logging import logger
from app.Api.router import api_router
from app.Auth.security import get_jwt_secret
from app.config import settings
from app.db.session import close_db, init_db
import redis.asyncio as redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup initiated")
    try:
        get_jwt_secret()
        init_db()

        app.state.redis = redis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
        await app.state.redis.ping()
        logger.info("Redis connected")
    except Exception:
        logger.exception("Application startup failed")
        r = getattr(app.state, "redis", None)
        if r:
            await r.aclose()
        close_db()
        raise

    logger.info("Application startup completed successfully")
    try:
        yield
    finally:
        logger.info("Application shutdown initiated")
        await app.state.redis.aclose()
        close_db()


app = FastAPI(lifespan=lifespan)

# 1. Define the Request Logging Middleware
class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process the request and get the response
        response = await call_next(request)

        # Calculate execution latency in milliseconds
        process_time_ms = (time.time() - start_time) * 1000

        # Log the structured request data
        logger.info(
            f"Method: {request.method} | "
            f"Path: {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Latency: {process_time_ms:.2f}ms"
        )
        return response


# 2. Register the middleware to the app
app.add_middleware(LogRequestsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    # You don't need manual logger.info("Server is running") anymore!
    return {"message": "the server is working"}


@app.get("/health")
def read_health():
    # Clean and automatic!
    return {"status": "ok"}

@app.get("/redis_health")
async def redis_health(request: Request):
    try:
        await request.app.state.redis.ping()
        return {"status": "ok", "redis": "ok"}
    except Exception:
        return {"status": "degraded", "redis": "down"}


app.include_router(api_router)

# main.py
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.middlewares.logging import logger
from app.Api.router import api_router
from app.Auth.security import get_jwt_secret
from app.middlewares.config import settings
from app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Application startup initiated")
    try:
        get_jwt_secret()
        init_db()
    except Exception:
        logger.exception("Application startup failed")
        close_db()
        raise

    logger.info("Application startup completed successfully")
    try:
        yield
    finally:
        logger.info("Application shutdown initiated")
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


app.include_router(api_router)

# main.py
import time
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.Core.logging import logger  # Direct clean import

app = FastAPI()


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


@app.on_event("startup")
async def startup():
    logger.info("Server is starting up")


@app.get("/")
def read_root():
    # You don't need manual logger.info("Server is running") anymore!
    return {"message": "the server is working"}


@app.get("/health")
def read_health():
    # Clean and automatic!
    return {"status": "ok"}

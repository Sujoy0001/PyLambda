from datetime import time
from fastapi import FastAPI, Request

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

from app.Core.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def read_root():
    logger.info("Server is running")
    return {"message": "the server is working"}

@app.get("/health")
def read_health():
    logger.info("Health check")
    return {"status": "ok"}
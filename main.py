# main.py
from fastapi import FastAPI
from app.Core.logging import logger  # Direct clean import

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("Server is starting up")

@app.get("/")
def read_root():
    logger.info("Server root endpoint hit")
    return {"message": "the server is working"}

@app.get("/health")
def read_health():
    logger.info("Health check endpoint hit")
    return {"status": "ok"}

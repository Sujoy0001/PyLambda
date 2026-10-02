# app/Core/logging.py
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = "app.log"


def _init_logger():
    # Using the root logger configuration applies it globally to FastAPI and Uvicorn
    logger = logging.getLogger("fastapi_app")

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )

        # Console Output
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

        # File Output
        file_out = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
        file_out.setFormatter(formatter)
        logger.addHandler(file_out)

    return logger


# Create the single instance that the rest of the app imports
logger = _init_logger()

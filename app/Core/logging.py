import logging
import sys

def setup_logging():
    log_format = '[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("Logs/app.log", encoding="utf-8")
        ],
        force=True
    )
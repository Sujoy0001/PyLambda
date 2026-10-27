from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import MetaData

from app.core.logging import logger


def _log_connection_created(
    dbapi_connection: object, connection_record: object
) -> None:
    logger.info(
        "Database connection established",
        extra={
            "db_event": "connect",
            "connection_id": id(dbapi_connection),
        },
    )


def _log_connection_closed(
    dbapi_connection: object, connection_record: object
) -> None:
    logger.info(
        "Database connection closed",
        extra={
            "db_event": "close",
            "connection_id": id(dbapi_connection),
        },
    )


def configure_database_connection_logging(engine: Engine) -> None:
    event.listen(engine, "connect", _log_connection_created)
    event.listen(engine, "close", _log_connection_closed)


def initialize_database(engine: Engine, metadata: MetaData) -> None:
    try:
        logger.info("Checking database connection")
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        logger.info("Database connection is available")

        metadata.create_all(bind=engine)
    except SQLAlchemyError:
        logger.exception("Database connection or initialization failed")
        raise

    logger.info("Database schema initialized")


def close_database(engine: Engine) -> None:
    logger.info("Closing database connection pool")
    engine.dispose()
    logger.info("Database connection pool closed")

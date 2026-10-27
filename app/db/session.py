import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.Auth.models import User
from app.core.database_logging import (
    close_database as dispose_database,
    configure_database_connection_logging,
    initialize_database,
)

load_dotenv()

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL must be configured before starting "
                "the application"
            )

        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )

        is_sqlite = database_url.startswith("sqlite")
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        _engine = create_engine(
            database_url,
            connect_args=connect_args,
            poolclass=StaticPool if is_sqlite else None,
            pool_pre_ping=True,
        )
        configure_database_connection_logging(_engine)

    return _engine


def init_db() -> None:
    initialize_database(get_engine(), User.metadata)


def close_db() -> None:
    if _engine is not None:
        dispose_database(_engine)


def get_db() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session

"""
Database engine and session management for the Library Management System.

This module provides the SQLAlchemy engine, session factory, and a
context-managed session lifecycle utility suitable for desktop and
service-layer usage.

The implementation follows SQLAlchemy 2.0 style patterns.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from library_app.config.settings import get_settings


def create_db_engine() -> Engine:
    """Create and configure the SQLAlchemy engine.

    The engine is configured from application settings and supports
    SQLite by default. Additional database backends such as PostgreSQL
    can be used later by simply changing the `DATABASE_URL`.

    Returns:
        A configured SQLAlchemy `Engine` instance.
    """
    settings = get_settings()

    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    return engine


engine: Engine = create_db_engine()

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_session() -> Session:
    """Create and return a new database session.

    This function returns a raw session and is suitable for manual
    session lifecycle management in service or repository code.

    Returns:
        A new SQLAlchemy `Session` instance.
    """
    return SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of database operations.

    The session is committed if the managed block succeeds, rolled back
    if an exception occurs, and always closed afterward.

    Yields:
        An active SQLAlchemy `Session` object.

    Raises:
        Exception: Re-raises any exception that occurs inside the block
            after performing a rollback.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

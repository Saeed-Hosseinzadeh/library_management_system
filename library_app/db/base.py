"""
Unified metadata entry point for the database schema.

This module imports the SQLAlchemy Declarative Base along with all domain
models to ensure they are registered with the metadata object. This is
particularly useful for database initialization scripts and migration tools
like Alembic.

To create all tables programmatically:
    >>> from library_app.db.base import Base, engine
    >>> Base.metadata.create_all(bind=engine)
"""

from __future__ import annotations

# Export the Base class and the engine for easy accessibility
from library_app.db.session import engine
from library_app.db.models import (
    Base,
    Book,
    Magazine,
    Member,
    Librarian,
    Loan,
)

__all__ = [
    "Base",
    "engine",
    "Book",
    "Magazine",
    "Member",
    "Librarian",
    "Loan",
]

"""
Repository implementation for Book data access.

This module provides data access patterns for the Book entity using
SQLAlchemy 2.0 style queries.
"""

from __future__ import annotations

from typing import Sequence, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from library_app.db.models import Book


class BookRepository:
    """Manages database operations for the Book entity."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An active SQLAlchemy Session.
        """
        self._session = session

    def create(self, book: Book) -> Book:
        """Persist a new Book entity in the database.

        Args:
            book: The Book transient instance to save.

        Returns:
            The persisted Book entity with its primary key populated.
        """
        self._session.add(book)
        return book

    def get_by_id(self, book_id: int) -> Optional[Book]:
        """Retrieve a Book by its primary key.

        Args:
            book_id: The ID of the book.

        Returns:
            The Book entity if found, otherwise None.
        """
        return self._session.get(Book, book_id)

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Retrieve a Book by its unique ISBN.

        Args:
            isbn: The normalized ISBN string.

        Returns:
            The Book entity if found, otherwise None.
        """
        stmt = select(Book).where(Book.isbn == isbn)
        return self._session.scalars(stmt).first()

    def get_all(self) -> Sequence[Book]:
        """Retrieve all Book entities from the database.

        Returns:
            A sequence containing all Books.
        """
        stmt = select(Book).order_by(Book.title)
        return self._session.scalars(stmt).all()

    def search_by_title_or_author(self, query: str) -> Sequence[Book]:
        """Search books containing a query string in the title or author.

        Args:
            query: The substring search keyword.

        Returns:
            A sequence of matching Book entities.
        """
        pattern = f"%{query}%"
        stmt = (
            select(Book)
            .where((Book.title.like(pattern)) | (Book.author.like(pattern)))
            .order_by(Book.title)
        )
        return self._session.scalars(stmt).all()

    def delete(self, book: Book) -> None:
        """Remove a Book entity from the database.

        Args:
            book: The persistent Book entity to delete.
        """
        self._session.delete(book)

    def delete_by_id(self, book_id: int) -> bool:
        """Remove a Book by its primary key.

        Args:
            book_id: The ID of the book to delete.

        Returns:
            True if the book was found and deleted, False otherwise.
        """
        book = self.get_by_id(book_id)
        if book:
            self.delete(book)
            return True
        return False

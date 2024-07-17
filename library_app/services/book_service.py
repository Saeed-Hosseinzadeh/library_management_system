"""
Business service for managing books.

This module encapsulates business rules and transactional workflows for
book-related operations. It validates user input, coordinates repository
access, and raises domain-specific exceptions instead of leaking raw ORM
or database concerns into higher layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from library_app.db.models import Book
from library_app.db.session import session_scope
from library_app.domain.exceptions import BookNotFoundError, DuplicateISBNError
from library_app.domain.validators import (
    validate_isbn,
    validate_non_empty_string,
)
from library_app.repositories.book_repository import BookRepository


@dataclass(slots=True, frozen=True)
class BookCreateData:
    """Input data required to create a new book.

    Attributes:
        title: Book title.
        author: Book author.
        isbn: ISBN-10 or ISBN-13.
        publisher: Optional publisher name.
        category: Optional category or genre.
        publication_year: Optional publication year.
        copies_total: Total number of copies available in inventory.
    """

    title: str
    author: str
    isbn: str
    publisher: Optional[str] = None
    category: Optional[str] = None
    publication_year: Optional[int] = None
    copies_total: int = 1


@dataclass(slots=True, frozen=True)
class BookUpdateData:
    """Input data for partial book updates.

    Any field set to ``None`` is ignored by the update workflow except
    for fields that are explicitly intended to remain nullable in your
    model. This keeps the API safe and predictable for controller usage.

    Attributes:
        title: Updated title.
        author: Updated author.
        isbn: Updated ISBN.
        publisher: Updated publisher.
        category: Updated category or genre.
        publication_year: Updated publication year.
        copies_total: Updated total number of copies.
    """

    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    category: Optional[str] = None
    publication_year: Optional[int] = None
    copies_total: Optional[int] = None


class BookService:
    """Service layer for book business operations."""

    def add_book(self, data: BookCreateData) -> Book:
        """Create a new book after applying business validation.

        This workflow validates required fields, normalizes the ISBN,
        verifies uniqueness, and persists the new entity inside a single
        transaction.

        Args:
            data: Structured input data for the new book.

        Returns:
            The newly created persistent Book entity.

        Raises:
            DuplicateISBNError: If another book already uses the same ISBN.
            ValueError: If copies_total or publication_year are invalid.
        """
        title = validate_non_empty_string(
            value=data.title,
            field_name="title",
            min_length=1,
            max_length=255,
        )
        author = validate_non_empty_string(
            value=data.author,
            field_name="author",
            min_length=1,
            max_length=255,
        )
        isbn = validate_isbn(data.isbn)

        publisher = None
        if data.publisher is not None and data.publisher.strip():
            publisher = validate_non_empty_string(
                value=data.publisher,
                field_name="publisher",
                min_length=1,
                max_length=255,
            )

        category = None
        if data.category is not None and data.category.strip():
            category = validate_non_empty_string(
                value=data.category,
                field_name="category",
                min_length=1,
                max_length=100,
            )

        if data.copies_total < 1:
            raise ValueError("copies_total must be at least 1.")

        if data.publication_year is not None and data.publication_year <= 0:
            raise ValueError("publication_year must be a positive integer.")

        with session_scope() as session:
            repository = BookRepository(session)

            existing = repository.get_by_isbn(isbn)
            if existing is not None:
                raise DuplicateISBNError(f"A book with ISBN '{isbn}' already exists.")

            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                category=category,
                publication_year=data.publication_year,
                copies_total=data.copies_total,
            )
            repository.create(book)
            session.flush()
            session.refresh(book)
            return book

    def get_book_by_id(self, book_id: int) -> Book:
        """Retrieve a book by primary key.

        Args:
            book_id: Database primary key.

        Returns:
            The matching Book entity.

        Raises:
            BookNotFoundError: If no book exists with the given ID.
        """
        with session_scope() as session:
            repository = BookRepository(session)
            book = repository.get_by_id(book_id)
            if book is None:
                raise BookNotFoundError(f"Book with id '{book_id}' was not found.")
            return book

    def get_book_by_isbn(self, isbn: str) -> Book:
        """Retrieve a book by ISBN.

        Args:
            isbn: Raw or normalized ISBN input.

        Returns:
            The matching Book entity.

        Raises:
            BookNotFoundError: If no book exists with the given ISBN.
        """
        normalized_isbn = validate_isbn(isbn)

        with session_scope() as session:
            repository = BookRepository(session)
            book = repository.get_by_isbn(normalized_isbn)
            if book is None:
                raise BookNotFoundError(
                    f"Book with ISBN '{normalized_isbn}' was not found."
                )
            return book

    def list_books(self) -> list[Book]:
        """Return all books ordered by repository default sorting.

        Returns:
            A list of Book entities.
        """
        with session_scope() as session:
            repository = BookRepository(session)
            return list(repository.get_all())

    def search_books(self, query: str) -> list[Book]:
        """Search books by title or author.

        Args:
            query: User-provided search term.

        Returns:
            A list of matching books.
        """
        normalized_query = validate_non_empty_string(
            value=query,
            field_name="query",
            min_length=1,
            max_length=255,
        )

        with session_scope() as session:
            repository = BookRepository(session)
            return list(repository.search_by_title_or_author(normalized_query))

    def update_book(self, book_id: int, data: BookUpdateData) -> Book:
        """Update an existing book with validated partial fields.

        Args:
            book_id: Primary key of the target book.
            data: Partial update payload.

        Returns:
            The updated Book entity.

        Raises:
            BookNotFoundError: If the target book does not exist.
            DuplicateISBNError: If the updated ISBN conflicts with another book.
            ValueError: If numeric fields are invalid.
        """
        with session_scope() as session:
            repository = BookRepository(session)
            book = repository.get_by_id(book_id)
            if book is None:
                raise BookNotFoundError(f"Book with id '{book_id}' was not found.")

            if data.title is not None:
                book.title = validate_non_empty_string(
                    value=data.title,
                    field_name="title",
                    min_length=1,
                    max_length=255,
                )

            if data.author is not None:
                book.author = validate_non_empty_string(
                    value=data.author,
                    field_name="author",
                    min_length=1,
                    max_length=255,
                )

            if data.isbn is not None:
                normalized_isbn = validate_isbn(data.isbn)
                existing = repository.get_by_isbn(normalized_isbn)
                if existing is not None and existing.id != book.id:
                    raise DuplicateISBNError(
                        f"A book with ISBN '{normalized_isbn}' already exists."
                    )
                book.isbn = normalized_isbn

            if data.publisher is not None:
                book.publisher = (
                    validate_non_empty_string(
                        value=data.publisher,
                        field_name="publisher",
                        min_length=1,
                        max_length=255,
                    )
                    if data.publisher.strip()
                    else None
                )

            if data.category is not None:
                book.category = (
                    validate_non_empty_string(
                        value=data.category,
                        field_name="category",
                        min_length=1,
                        max_length=100,
                    )
                    if data.category.strip()
                    else None
                )

            if data.publication_year is not None:
                if data.publication_year <= 0:
                    raise ValueError("publication_year must be a positive integer.")
                book.publication_year = data.publication_year

            if data.copies_total is not None:
                if data.copies_total < 1:
                    raise ValueError("copies_total must be at least 1.")
                book.copies_total = data.copies_total

            session.flush()
            session.refresh(book)
            return book

    def delete_book(self, book_id: int) -> None:
        """Delete a book by ID.

        Args:
            book_id: Primary key of the target book.

        Raises:
            BookNotFoundError: If the book does not exist.
        """
        with session_scope() as session:
            repository = BookRepository(session)
            book = repository.get_by_id(book_id)
            if book is None:
                raise BookNotFoundError(f"Book with id '{book_id}' was not found.")
            repository.delete(book)

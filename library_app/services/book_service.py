from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from library_app.db.models import Book
from library_app.domain.exceptions import BookNotFoundError, DuplicateISBNError, ValidationError
from library_app.domain.validators import normalize_isbn, validate_non_empty_string
from library_app.repositories.book_repository import BookRepository


@dataclass(slots=True)
class BookCreateData:
    """Book creation payload."""

    title: str
    author: str
    isbn: str
    publisher: str | None = None
    category: str | None = None
    publication_year: int | None = None
    copies_total: int = 1
    quantity: int = 1


@dataclass(slots=True)
class BookUpdateData:
    """Book update payload."""

    title: str
    author: str
    isbn: str
    publisher: str | None = None
    category: str | None = None
    publication_year: int | None = None
    copies_total: int = 1
    quantity: int = 1


class BookService:
    """Book business logic."""

    def __init__(self, repository: BookRepository | None = None) -> None:
        self.repository = repository or BookRepository()

    def list(self, session: Session) -> Sequence[Book]:
        """Return all books."""
        statement = select(Book).order_by(Book.title.asc(), Book.id.asc())
        return session.execute(statement).scalars().all()

    def search(self, session: Session, query: str) -> Sequence[Book]:
        """Search books."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return self.list(session)
        return self.repository.search(session, cleaned_query)

    def add(self, session: Session, data: BookCreateData) -> Book:
        """Create a new book."""
        title = validate_non_empty_string(data.title, "title")
        author = validate_non_empty_string(data.author, "author")
        isbn = normalize_isbn(data.isbn)

        publisher = self._clean_optional(data.publisher)
        category = self._clean_optional(data.category)
        publication_year = self._validate_publication_year(data.publication_year)
        copies_total = self._validate_copies_total(data.copies_total)
        quantity = self._validate_quantity(data.quantity, copies_total)

        if self.repository.get_by_isbn(session, isbn):
            raise DuplicateISBNError("A book with this ISBN already exists.")

        book = Book(
            title=title,
            author=author,
            isbn=isbn,
            publisher=publisher,
            category=category,
            publication_year=publication_year,
            copies_total=copies_total,
            quantity=quantity,
        )
        return self.repository.add(session, book)

    def update(self, session: Session, book_id: int, data: BookUpdateData) -> Book:
        """Update an existing book."""
        book = self.repository.get_by_id(session, book_id)
        if book is None:
            raise BookNotFoundError("Book not found.")

        title = validate_non_empty_string(data.title, "title")
        author = validate_non_empty_string(data.author, "author")
        isbn = normalize_isbn(data.isbn)

        existing = self.repository.get_by_isbn(session, isbn)
        if existing is not None and existing.id != book.id:
            raise DuplicateISBNError("A book with this ISBN already exists.")

        publisher = self._clean_optional(data.publisher)
        category = self._clean_optional(data.category)
        publication_year = self._validate_publication_year(data.publication_year)
        copies_total = self._validate_copies_total(data.copies_total)
        quantity = self._validate_quantity(data.quantity, copies_total)

        book.title = title
        book.author = author
        book.isbn = isbn
        book.publisher = publisher
        book.category = category
        book.publication_year = publication_year
        book.copies_total = copies_total
        book.quantity = quantity

        session.flush()
        return book

    def remove(self, session: Session, book_id: int) -> None:
        """Delete a book."""
        book = self.repository.get_by_id(session, book_id)
        if book is None:
            raise BookNotFoundError("Book not found.")
        self.repository.delete(session, book)

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        """Normalize optional text fields."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @staticmethod
    def _validate_publication_year(value: int | None) -> int | None:
        """Validate publication year."""
        if value is None:
            return None
        if value <= 0:
            raise ValidationError("publication_year must be greater than zero.")
        return value

    @staticmethod
    def _validate_copies_total(value: int) -> int:
        """Validate total copies."""
        if value < 0:
            raise ValidationError("copies_total cannot be negative.")
        return value

    @staticmethod
    def _validate_quantity(quantity: int, copies_total: int) -> int:
        """Validate available quantity."""
        if quantity < 0:
            raise ValidationError("quantity cannot be negative.")
        if quantity > copies_total:
            raise ValidationError("quantity cannot be greater than copies_total.")
        return quantity

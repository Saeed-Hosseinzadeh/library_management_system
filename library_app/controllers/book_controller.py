from __future__ import annotations

import logging
from typing import Sequence

from library_app.controllers.base_controller import ControllerResult
from library_app.db.models import Book
from library_app.db.session import session_scope
from library_app.domain.exceptions import BookNotFoundError, DuplicateISBNError, ValidationError
from library_app.services.book_service import BookCreateData, BookService, BookUpdateData

logger = logging.getLogger(__name__)


class BookController:
    """Book controller."""

    def __init__(self, service: BookService | None = None) -> None:
        self.service = service or BookService()

    def list_books(self) -> ControllerResult[Sequence[Book]]:
        """Return all books."""
        try:
            with session_scope() as session:
                books = self.service.list(session)
                return ControllerResult.ok(books)
        except Exception:
            logger.exception("Failed to list books.")
            return ControllerResult.fail("Failed to list books.")

    def search_books(self, query: str) -> ControllerResult[Sequence[Book]]:
        """Search books."""
        try:
            with session_scope() as session:
                books = self.service.search(session, query)
                return ControllerResult.ok(books)
        except Exception:
            logger.exception("Failed to search books.")
            return ControllerResult.fail("Failed to search books.")

    def add_book(
        self,
        title: str,
        author: str,
        isbn: str,
        publisher: str | None = None,
        category: str | None = None,
        publication_year: int | None = None,
        copies_total: int = 1,
        quantity: int = 1,
    ) -> ControllerResult[Book]:
        """Create a book."""
        try:
            payload = BookCreateData(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                category=category,
                publication_year=publication_year,
                copies_total=copies_total,
                quantity=quantity,
            )
            with session_scope() as session:
                book = self.service.add(session, payload)
                return ControllerResult.ok(book, "Book created successfully.")
        except (ValidationError, DuplicateISBNError) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to add book.")
            return ControllerResult.fail("Failed to add book.")

    def update_book(
        self,
        book_id: int,
        title: str,
        author: str,
        isbn: str,
        publisher: str | None = None,
        category: str | None = None,
        publication_year: int | None = None,
        copies_total: int = 1,
        quantity: int = 1,
    ) -> ControllerResult[Book]:
        """Update a book."""
        try:
            payload = BookUpdateData(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                category=category,
                publication_year=publication_year,
                copies_total=copies_total,
                quantity=quantity,
            )
            with session_scope() as session:
                book = self.service.update(session, book_id, payload)
                return ControllerResult.ok(book, "Book updated successfully.")
        except (ValidationError, DuplicateISBNError, BookNotFoundError) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to update book.")
            return ControllerResult.fail("Failed to update book.")

    def remove_book(self, book_id: int) -> ControllerResult[None]:
        """Delete a book."""
        try:
            with session_scope() as session:
                self.service.remove(session, book_id)
                return ControllerResult.ok(message="Book removed successfully.")
        except (ValidationError, BookNotFoundError) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to remove book.")
            return ControllerResult.fail("Failed to remove book.")

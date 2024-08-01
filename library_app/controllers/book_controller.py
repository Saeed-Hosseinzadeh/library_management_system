"""
Controller for handling book-related UI requests.
"""

from __future__ import annotations

import logging
from typing import Sequence

from library_app.controllers.base_controller import ControllerResult
from library_app.db.models import Book
from library_app.domain.exceptions import BookNotFoundError, DuplicateISBNError
from library_app.services.book_service import (
    BookCreateData,
    BookService,
    BookUpdateData,
)

logger = logging.getLogger(__name__)


class BookController:
    """Coordinates UI requests for books with the BookService."""

    def __init__(self, book_service: BookService) -> None:
        """Initialize the controller with its backing service."""
        self._service = book_service

    def add_book(
        self,
        title: str,
        author: str,
        isbn: str,
        publisher: str = "",
        category: str = "",
        publication_year: str = "",
        copies_total: int = 1,
    ) -> ControllerResult[Book]:
        """Validate input parameters and request book creation."""
        try:
            pub_year_int = None
            if publication_year.strip():
                try:
                    pub_year_int = int(publication_year)
                except ValueError:
                    return ControllerResult.fail("Publication year must be a valid number.")

            data = BookCreateData(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher.strip() or None,
                category=category.strip() or None,
                publication_year=pub_year_int,
                copies_total=copies_total,
            )

            book = self._service.add_book(data)
            return ControllerResult.ok(book, f"Book '{book.title}' added successfully.")

        except DuplicateISBNError as e:
            return ControllerResult.fail(str(e))
        except ValueError as e:
            return ControllerResult.fail(f"Validation error: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error in BookController.add_book")
            return ControllerResult.fail(f"An unexpected error occurred: {str(e)}")

    def get_all_books(self) -> ControllerResult[Sequence[Book]]:
        """Retrieve all books registered in the system."""
        try:
            books = self._service.list_books()
            return ControllerResult.ok(books)
        except Exception as e:
            logger.exception("Failed to retrieve books")
            return ControllerResult.fail(f"Could not retrieve book list: {str(e)}")

    def search_books(self, query: str) -> ControllerResult[Sequence[Book]]:
        """Search books matching the provided query string."""
        if not query.strip():
            return self.get_all_books()
        try:
            results = self._service.search_books(query)
            return ControllerResult.ok(results)
        except ValueError as e:
            return ControllerResult.fail(f"Search parameter error: {str(e)}")
        except Exception as e:
            logger.exception("Search operation failed")
            return ControllerResult.fail(f"An error occurred while searching: {str(e)}")

    def update_book(
        self,
        book_id: int,
        title: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        publisher: str | None = None,
        category: str | None = None,
        publication_year: str | None = None,
        copies_total: int | None = None,
    ) -> ControllerResult[Book]:
        """Request modifications to an existing book record."""
        try:
            pub_year_int = None
            if publication_year is not None and publication_year.strip():
                try:
                    pub_year_int = int(publication_year)
                except ValueError:
                    return ControllerResult.fail("Publication year must be a valid number.")

            data = BookUpdateData(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                category=category,
                publication_year=pub_year_int,
                copies_total=copies_total,
            )

            updated_book = self._service.update_book(book_id, data)
            return ControllerResult.ok(updated_book, "Book updated successfully.")

        except BookNotFoundError as e:
            return ControllerResult.fail(str(e))
        except DuplicateISBNError as e:
            return ControllerResult.fail(str(e))
        except ValueError as e:
            return ControllerResult.fail(f"Validation error: {str(e)}")
        except Exception as e:
            logger.exception("Error updating book")
            return ControllerResult.fail(f"Update failed: {str(e)}")

    def delete_book(self, book_id: int) -> ControllerResult[None]:
        """Remove a book from the library catalog."""
        try:
            self._service.delete_book(book_id)
            return ControllerResult.ok(message="Book deleted successfully.")
        except BookNotFoundError as e:
            return ControllerResult.fail(str(e))
        except Exception as e:
            logger.exception("Error deleting book")
            return ControllerResult.fail(f"Deletion failed: {str(e)}")

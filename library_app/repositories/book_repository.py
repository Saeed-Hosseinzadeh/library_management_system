from __future__ import annotations

from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from library_app.db.models import Book


class BookRepository:
    """Persistence operations for books."""

    def get_by_id(self, session: Session, id: int) -> Book | None:
        """Return a book by primary key."""
        return session.get(Book, id)

    def get_by_isbn(self, session: Session, isbn: str) -> Book | None:
        """Return a book by ISBN."""
        statement = select(Book).where(Book.isbn == isbn)
        return session.execute(statement).scalar_one_or_none()

    def search(self, session: Session, query: str) -> Sequence[Book]:
        """Search books by title, author, ISBN, publisher, or category."""
        term = f"%{query.strip()}%"
        statement = (
            select(Book)
            .where(
                or_(
                    Book.title.ilike(term),
                    Book.author.ilike(term),
                    Book.isbn.ilike(term),
                    Book.publisher.ilike(term),
                    Book.category.ilike(term),
                )
            )
            .order_by(Book.title.asc(), Book.id.asc())
        )
        return session.execute(statement).scalars().all()

    def add(self, session: Session, book: Book) -> Book:
        """Add a book to the session."""
        session.add(book)
        session.flush()
        return book

    def delete(self, session: Session, book: Book) -> None:
        """Delete a book from the session."""
        session.delete(book)
        session.flush()

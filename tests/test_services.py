"""
Integration-style unit tests for the service layer.

This module tests the core business workflows of the Library Management
System using an isolated in-memory SQLite database. The tests validate
that services correctly enforce domain rules, persist data, and raise
custom exceptions when business constraints are violated.

The tests intentionally use real SQLAlchemy ORM operations instead of
mocking repositories so that service behavior, transaction handling,
and model persistence are verified together.
"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from datetime import date
from typing import Generator
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from library_app.db.models import Base, Book, Loan, Member
from library_app.domain.exceptions import (
    BookAlreadyLoanedError,
    DuplicateISBNError,
)
from library_app.services.book_service import BookCreateData, BookService
from library_app.services.loan_service import BorrowBookData, LoanService
from library_app.services.member_service import MemberCreateData, MemberService


class TestServiceLayer(unittest.TestCase):
    """Test suite for book, member, and loan service workflows."""

    engine = None
    SessionLocal = None

    @classmethod
    def setUpClass(cls) -> None:
        """Create the in-memory database schema once for the test class."""
        cls.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            future=True,
            echo=False,
        )
        cls.SessionLocal = sessionmaker(
            bind=cls.engine,
            class_=Session,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        """Dispose the test database engine after all tests complete."""
        if cls.engine is not None:
            cls.engine.dispose()

    def setUp(self) -> None:
        """Reset database contents and initialize services before each test."""
        self._clear_database()

        self.book_service = BookService()
        self.member_service = MemberService()
        self.loan_service = LoanService()

        self.book_service_patcher = patch(
            "library_app.services.book_service.session_scope",
            self._test_session_scope,
        )
        self.member_service_patcher = patch(
            "library_app.services.member_service.session_scope",
            self._test_session_scope,
        )
        self.loan_service_patcher = patch(
            "library_app.services.loan_service.session_scope",
            self._test_session_scope,
        )

        self.book_service_patcher.start()
        self.member_service_patcher.start()
        self.loan_service_patcher.start()

    def tearDown(self) -> None:
        """Stop service session patchers after each test."""
        self.book_service_patcher.stop()
        self.member_service_patcher.stop()
        self.loan_service_patcher.stop()

    @contextmanager
    def _test_session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional session bound to the in-memory test engine.

        This helper mirrors the production `session_scope()` contract so
        service modules can be tested without modifying production code.

        Yields:
            An active SQLAlchemy Session bound to the test engine.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _clear_database(self) -> None:
        """Delete all rows from test tables to isolate each test case."""
        if self.SessionLocal is None:
            raise RuntimeError("Test session factory is not initialized.")

        with self.SessionLocal() as session:
            session.execute(Loan.__table__.delete())
            session.execute(Book.__table__.delete())
            session.execute(Member.__table__.delete())
            session.commit()

    def test_add_book_and_register_member_successfully(self) -> None:
        """Verify a book and a member can be created successfully."""
        created_book = self.book_service.add_book(
            BookCreateData(
                title="Clean Code",
                author="Robert C. Martin",
                isbn="978-0-13-235088-4",
                publisher="Prentice Hall",
                category="Software Engineering",
                publication_year=2008,
                copies_total=1,
            )
        )

        created_member = self.member_service.register_member(
            MemberCreateData(
                name="Ali Rezaei",
                member_id="MEMBER_001",
                phone="09123456789",
                address="Tehran, Iran",
            )
        )

        self.assertIsNotNone(created_book.id)
        self.assertEqual(created_book.title, "Clean Code")
        self.assertEqual(created_book.author, "Robert C. Martin")
        self.assertEqual(created_book.isbn, "9780132350884")

        self.assertIsNotNone(created_member.id)
        self.assertEqual(created_member.name, "Ali Rezaei")
        self.assertEqual(created_member.member_id, "MEMBER_001")
        self.assertEqual(created_member.phone, "09123456789")

        with self.SessionLocal() as session:
            persisted_book = session.get(Book, created_book.id)
            persisted_member = session.get(Member, created_member.id)

            self.assertIsNotNone(persisted_book)
            self.assertIsNotNone(persisted_member)
            self.assertEqual(persisted_book.isbn, "9780132350884")
            self.assertEqual(persisted_member.member_id, "MEMBER_001")

    def test_add_book_raises_duplicate_isbn_error(self) -> None:
        """Verify duplicate ISBN creation attempts raise DuplicateISBNError."""
        self.book_service.add_book(
            BookCreateData(
                title="Domain-Driven Design",
                author="Eric Evans",
                isbn="978-0-321-12521-7",
                publisher="Addison-Wesley",
                category="Architecture",
                publication_year=2003,
                copies_total=1,
            )
        )

        with self.assertRaises(DuplicateISBNError):
            self.book_service.add_book(
                BookCreateData(
                    title="DDD Duplicate",
                    author="Another Author",
                    isbn="9780321125217",
                    publisher="Test Publisher",
                    category="Architecture",
                    publication_year=2024,
                    copies_total=1,
                )
            )

    def test_borrow_book_success_and_prevent_double_borrow(self) -> None:
        """Verify borrowing creates a loan and blocks a second active loan."""
        created_book = self.book_service.add_book(
            BookCreateData(
                title="The Pragmatic Programmer",
                author="Andrew Hunt",
                isbn="978-0-201-61622-4",
                publisher="Addison-Wesley",
                category="Programming",
                publication_year=1999,
                copies_total=1,
            )
        )

        first_member = self.member_service.register_member(
            MemberCreateData(
                name="Sara Ahmadi",
                member_id="MEMBER_100",
                phone="09121234567",
                address="Shiraz, Iran",
            )
        )

        second_member = self.member_service.register_member(
            MemberCreateData(
                name="Reza Karimi",
                member_id="MEMBER_101",
                phone="09129876543",
                address="Tabriz, Iran",
            )
        )

        created_loan = self.loan_service.borrow_book(
            BorrowBookData(
                book_id=created_book.id,
                member_id=first_member.id,
                loan_date=date(2026, 1, 10),
                due_date=date(2026, 1, 24),
            )
        )

        self.assertIsNotNone(created_loan.id)
        self.assertEqual(created_loan.book_id, created_book.id)
        self.assertEqual(created_loan.member_id, first_member.id)
        self.assertEqual(created_loan.loan_date, date(2026, 1, 10))
        self.assertEqual(created_loan.due_date, date(2026, 1, 24))
        self.assertIsNone(created_loan.return_date)

        with self.SessionLocal() as session:
            stmt = select(Loan).where(Loan.id == created_loan.id)
            persisted_loan = session.scalars(stmt).first()

            self.assertIsNotNone(persisted_loan)
            self.assertEqual(persisted_loan.book_id, created_book.id)
            self.assertEqual(persisted_loan.member_id, first_member.id)
            self.assertIsNone(persisted_loan.return_date)

        with self.assertRaises(BookAlreadyLoanedError):
            self.loan_service.borrow_book(
                BorrowBookData(
                    book_id=created_book.id,
                    member_id=second_member.id,
                    loan_date=date(2026, 1, 11),
                    due_date=date(2026, 1, 25),
                )
            )

    def test_return_book_successfully_updates_return_date(self) -> None:
        """Verify returning a book sets the loan return_date correctly."""
        created_book = self.book_service.add_book(
            BookCreateData(
                title="Refactoring",
                author="Martin Fowler",
                isbn="978-0-13-475759-9",
                publisher="Addison-Wesley",
                category="Software Engineering",
                publication_year=2018,
                copies_total=1,
            )
        )

        created_member = self.member_service.register_member(
            MemberCreateData(
                name="Nima Hosseini",
                member_id="MEMBER_200",
                phone="09125554433",
                address="Mashhad, Iran",
            )
        )

        created_loan = self.loan_service.borrow_book(
            BorrowBookData(
                book_id=created_book.id,
                member_id=created_member.id,
                loan_date=date(2026, 2, 1),
                due_date=date(2026, 2, 15),
            )
        )

        returned_loan = self.loan_service.return_book(
            loan_id=created_loan.id,
            return_date=date(2026, 2, 10),
        )

        self.assertEqual(returned_loan.id, created_loan.id)
        self.assertEqual(returned_loan.return_date, date(2026, 2, 10))

        with self.SessionLocal() as session:
            persisted_loan = session.get(Loan, created_loan.id)
            self.assertIsNotNone(persisted_loan)
            self.assertEqual(persisted_loan.return_date, date(2026, 2, 10))

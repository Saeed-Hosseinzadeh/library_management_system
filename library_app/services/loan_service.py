"""
Business service for managing book loan transactions.

This module implements the central borrowing and return workflows of the
library domain. It ensures that books and members exist, prevents double
loaning of the same book while active, and records returns consistently
using domain-specific exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import and_, select

from library_app.db.models import Book, Loan, Member
from library_app.db.session import session_scope
from library_app.domain.exceptions import (
    BookAlreadyLoanedError,
    BookNotFoundError,
    InvalidReturnError,
    LoanNotFoundError,
    MemberNotFoundError,
)


@dataclass(slots=True, frozen=True)
class BorrowBookData:
    """Input data for creating a new loan transaction.

    Attributes:
        book_id: Database primary key of the book to loan.
        member_id: Database primary key of the member borrowing the book.
        loan_date: Loan start date. Defaults to today's date when omitted.
        due_date: Optional due date. If omitted, the service can derive it
            from a default borrowing period.
        loan_period_days: Default borrowing period used when due_date is not
            explicitly provided.
    """

    book_id: int
    member_id: int
    loan_date: Optional[date] = None
    due_date: Optional[date] = None
    loan_period_days: int = 14


class LoanService:
    """Service layer for loan and return business operations."""

    def borrow_book(self, data: BorrowBookData) -> Loan:
        """Borrow a book for a member.

        This workflow validates the existence of the book and member,
        checks that the book is not already actively loaned out, and then
        creates a new Loan record inside a single transaction.

        Args:
            data: Structured input for the borrowing operation.

        Returns:
            The newly created Loan entity.

        Raises:
            BookNotFoundError: If the target book does not exist.
            MemberNotFoundError: If the target member does not exist.
            BookAlreadyLoanedError: If the book currently has an active loan.
            ValueError: If date inputs are invalid.
        """
        if data.loan_period_days < 1:
            raise ValueError("loan_period_days must be at least 1.")

        effective_loan_date = data.loan_date or date.today()
        effective_due_date = data.due_date or (
            effective_loan_date + timedelta(days=data.loan_period_days)
        )

        if effective_due_date < effective_loan_date:
            raise ValueError("due_date must be greater than or equal to loan_date.")

        with session_scope() as session:
            book = session.get(Book, data.book_id)
            if book is None:
                raise BookNotFoundError(f"Book with id '{data.book_id}' was not found.")

            member = session.get(Member, data.member_id)
            if member is None:
                raise MemberNotFoundError(
                    f"Member with id '{data.member_id}' was not found."
                )

            active_loan_stmt = select(Loan).where(
                and_(
                    Loan.book_id == book.id,
                    Loan.return_date.is_(None),
                )
            )
            active_loan = session.scalars(active_loan_stmt).first()
            if active_loan is not None:
                raise BookAlreadyLoanedError(
                    f"Book with id '{book.id}' is already loaned out."
                )

            loan = Loan(
                book_id=book.id,
                member_id=member.id,
                loan_date=effective_loan_date,
                due_date=effective_due_date,
                return_date=None,
            )
            session.add(loan)
            session.flush()
            session.refresh(loan)
            return loan

    def return_book(self, loan_id: int, return_date: Optional[date] = None) -> Loan:
        """Mark an active loan as returned.

        Args:
            loan_id: Primary key of the loan transaction.
            return_date: Optional return date. Defaults to today's date.

        Returns:
            The updated Loan entity.

        Raises:
            LoanNotFoundError: If the loan does not exist.
            InvalidReturnError: If the loan is already returned or the
                return date is inconsistent.
        """
        effective_return_date = return_date or date.today()

        with session_scope() as session:
            loan = session.get(Loan, loan_id)
            if loan is None:
                raise LoanNotFoundError(f"Loan with id '{loan_id}' was not found.")

            if loan.return_date is not None:
                raise InvalidReturnError(
                    f"Loan with id '{loan_id}' has already been returned."
                )

            if effective_return_date < loan.loan_date:
                raise InvalidReturnError(
                    "return_date cannot be earlier than the original loan_date."
                )

            loan.return_date = effective_return_date
            session.flush()
            session.refresh(loan)
            return loan

    def get_active_loan_by_book_id(self, book_id: int) -> Loan:
        """Retrieve the active loan record for a given book.

        Args:
            book_id: Database primary key of the book.

        Returns:
            The active Loan entity for the book.

        Raises:
            LoanNotFoundError: If the book has no active loan.
        """
        with session_scope() as session:
            stmt = select(Loan).where(
                and_(
                    Loan.book_id == book_id,
                    Loan.return_date.is_(None),
                )
            )
            loan = session.scalars(stmt).first()
            if loan is None:
                raise LoanNotFoundError(
                    f"No active loan found for book id '{book_id}'."
                )
            return loan

    def list_active_loans(self) -> list[Loan]:
        """Return all active loan records.

        Returns:
            A list of active Loan entities.
        """
        with session_scope() as session:
            stmt = select(Loan).where(Loan.return_date.is_(None)).order_by(Loan.loan_date)
            return list(session.scalars(stmt).all())

    def list_member_loans(
        self,
        member_id: int,
        active_only: bool = False,
    ) -> list[Loan]:
        """List loans for a given member.

        Args:
            member_id: Database primary key of the member.
            active_only: Whether to limit results to active loans.

        Returns:
            A list of Loan entities for the member.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        with session_scope() as session:
            member = session.get(Member, member_id)
            if member is None:
                raise MemberNotFoundError(
                    f"Member with id '{member_id}' was not found."
                )

            stmt = select(Loan).where(Loan.member_id == member.id)
            if active_only:
                stmt = stmt.where(Loan.return_date.is_(None))

            stmt = stmt.order_by(Loan.loan_date.desc())
            return list(session.scalars(stmt).all())

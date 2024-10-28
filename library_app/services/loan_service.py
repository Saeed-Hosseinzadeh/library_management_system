from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from library_app.db.models import Book, Loan, Member
from library_app.domain.exceptions import (
    BookAlreadyLoanedError,
    BookNotFoundError,
    LoanNotFoundError,
    MemberNotFoundError,
    ValidationError,
)
from library_app.domain.validators import normalize_isbn, validate_identifier
from library_app.repositories.book_repository import BookRepository
from library_app.repositories.loan_repository import LoanRepository
from library_app.repositories.member_repository import MemberRepository


@dataclass(slots=True)
class BorrowBookData:
    """Loan creation payload."""

    member_id: str
    isbn: str


class LoanService:
    """Loan business logic."""

    def __init__(
        self,
        loan_repository: LoanRepository | None = None,
        book_repository: BookRepository | None = None,
        member_repository: MemberRepository | None = None,
    ) -> None:
        self.loan_repository = loan_repository or LoanRepository()
        self.book_repository = book_repository or BookRepository()
        self.member_repository = member_repository or MemberRepository()

    def get_active_loans(self, session: Session) -> Sequence[Loan]:
        """Return active loans."""
        return self.loan_repository.get_active_loans(session)

    def issue_loan(self, session: Session, data: BorrowBookData) -> Loan:
        """Create a loan and decrement available quantity."""
        member_identifier = validate_identifier(data.member_id, "member_id")
        isbn = normalize_isbn(data.isbn)

        member = self.member_repository.get_by_member_id(session, member_identifier)
        if member is None:
            raise MemberNotFoundError("Member not found.")

        book = self.book_repository.get_by_isbn(session, isbn)
        if book is None:
            raise BookNotFoundError("Book not found.")

        if book.quantity <= 0:
            raise ValidationError("No available copies for this book.")

        active_loan_statement = select(Loan).where(
            Loan.member_id == member.id,
            Loan.book_id == book.id,
            Loan.return_date.is_(None),
        )
        active_loan = session.execute(active_loan_statement).scalar_one_or_none()
        if active_loan is not None:
            raise BookAlreadyLoanedError("This member already has an active loan for this book.")

        loan = Loan(
            book_id=book.id,
            member_id=member.id,
            loan_date=date.today(),
            return_date=None,
        )
        self.loan_repository.add(session, loan)

        book.quantity -= 1
        session.flush()
        session.refresh(
            loan,
            attribute_names=["book", "member"],
        )
        return self._reload_loan(session, loan.id)

    def terminate_loan(self, session: Session, loan_id: int) -> Loan:
        """Close a loan and increment available quantity."""
        loan = self.loan_repository.get_by_id(session, loan_id)
        if loan is None:
            raise LoanNotFoundError("Loan not found.")

        if loan.return_date is not None:
            raise ValidationError("Loan is already terminated.")

        book = loan.book
        if book is None:
            book = self.book_repository.get_by_id(session, loan.book_id)
            if book is None:
                raise BookNotFoundError("Book not found.")

        loan.return_date = date.today()
        book.quantity += 1

        if book.quantity > book.copies_total:
            raise ValidationError("quantity cannot be greater than copies_total.")

        session.flush()
        return self._reload_loan(session, loan.id)

    @staticmethod
    def _reload_loan(session: Session, loan_id: int) -> Loan:
        """Reload a loan with eager-loaded relations."""
        statement = (
            select(Loan)
            .options(
                joinedload(Loan.book),
                joinedload(Loan.member),
            )
            .where(Loan.id == loan_id)
        )
        loan = session.execute(statement).scalar_one_or_none()
        if loan is None:
            raise LoanNotFoundError("Loan not found.")
        return loan

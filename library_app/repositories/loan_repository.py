from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from library_app.db.models import Loan


class LoanRepository:
    """Persistence operations for loans."""

    def get_active_loans(self, session: Session) -> Sequence[Loan]:
        """Return all active loans with eager-loaded book and member relations."""
        statement = (
            select(Loan)
            .options(
                joinedload(Loan.book),
                joinedload(Loan.member),
            )
            .where(Loan.return_date.is_(None))
            .order_by(Loan.loan_date.desc(), Loan.id.desc())
        )
        return session.execute(statement).scalars().all()

    def get_by_id(self, session: Session, id: int) -> Loan | None:
        """Return a loan by primary key with eager-loaded relations."""
        statement = (
            select(Loan)
            .options(
                joinedload(Loan.book),
                joinedload(Loan.member),
            )
            .where(Loan.id == id)
        )
        return session.execute(statement).scalar_one_or_none()

    def add(self, session: Session, loan: Loan) -> Loan:
        """Add a loan to the session."""
        session.add(loan)
        session.flush()
        return loan
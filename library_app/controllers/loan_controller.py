from __future__ import annotations

import logging
from typing import Sequence

from library_app.controllers.base_controller import ControllerResult
from library_app.db.models import Loan
from library_app.db.session import session_scope
from library_app.domain.exceptions import (
    BookAlreadyLoanedError,
    BookNotFoundError,
    LoanNotFoundError,
    MemberNotFoundError,
    ValidationError,
)
from library_app.services.loan_service import BorrowBookData, LoanService

logger = logging.getLogger(__name__)


class LoanController:
    """Loan controller."""

    def __init__(self, service: LoanService | None = None) -> None:
        self.service = service or LoanService()

    def get_active_loans(self) -> ControllerResult[Sequence[Loan]]:
        """Return active loans."""
        try:
            with session_scope() as session:
                loans = self.service.get_active_loans(session)
                return ControllerResult.ok(loans)
        except Exception:
            logger.exception("Failed to load active loans.")
            return ControllerResult.fail("Failed to load active loans.")

    def issue_loan(self, member_id: str, isbn: str) -> ControllerResult[Loan]:
        """Issue a loan."""
        try:
            payload = BorrowBookData(member_id=member_id, isbn=isbn)
            with session_scope() as session:
                loan = self.service.issue_loan(session, payload)
                return ControllerResult.ok(loan, "Loan issued successfully.")
        except (
            ValidationError,
            MemberNotFoundError,
            BookNotFoundError,
            BookAlreadyLoanedError,
        ) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to issue loan.")
            return ControllerResult.fail("Failed to issue loan.")

    def terminate_loan(self, loan_id: int) -> ControllerResult[Loan]:
        """Terminate a loan."""
        try:
            with session_scope() as session:
                loan = self.service.terminate_loan(session, loan_id)
                return ControllerResult.ok(loan, "Loan terminated successfully.")
        except (
            ValidationError,
            LoanNotFoundError,
            BookNotFoundError,
        ) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to terminate loan.")
            return ControllerResult.fail("Failed to terminate loan.")

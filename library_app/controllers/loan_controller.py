"""
Controller for handling lending and returning UI requests.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Sequence

from library_app.controllers.base_controller import ControllerResult
from library_app.db.models import Loan
from library_app.domain.exceptions import (
    BookAlreadyLoanedError,
    BookNotFoundError,
    InvalidReturnError,
    LoanNotFoundError,
    MemberNotFoundError,
)
from library_app.services.loan_service import BorrowBookData, LoanService

logger = logging.getLogger(__name__)


class LoanController:
    """Coordinates active borrowing and return operations with LoanService."""

    def __init__(self, loan_service: LoanService) -> None:
        """Initialize the controller with its backing service."""
        self._service = loan_service

    def borrow_book(
        self,
        book_id: int,
        member_id: int,
        loan_date: date | None = None,
        due_date: date | None = None,
        loan_period_days: int = 14,
    ) -> ControllerResult[Loan]:
        """Coordinate a book borrowing workflow."""
        try:
            data = BorrowBookData(
                book_id=book_id,
                member_id=member_id,
                loan_date=loan_date,
                due_date=due_date,
                loan_period_days=loan_period_days,
            )
            loan = self._service.borrow_book(data)
            return ControllerResult.ok(loan, "Book successfully borrowed.")

        except (BookNotFoundError, MemberNotFoundError, BookAlreadyLoanedError) as e:
            return ControllerResult.fail(str(e))
        except ValueError as e:
            return ControllerResult.fail(f"Invalid input: {str(e)}")
        except Exception as e:
            logger.exception("Error creating loan")
            return ControllerResult.fail(f"Could not execute loan process: {str(e)}")

    def return_book(self, loan_id: int, return_date: date | None = None) -> ControllerResult[Loan]:
        """Coordinate a book return workflow."""
        try:
            loan = self._service.return_book(loan_id, return_date)
            return ControllerResult.ok(loan, "Book successfully returned.")
        except (LoanNotFoundError, InvalidReturnError) as e:
            return ControllerResult.fail(str(e))
        except Exception as e:
            logger.exception("Error returning book")
            return ControllerResult.fail(f"Could not process return: {str(e)}")

    def get_active_loans(self) -> ControllerResult[Sequence[Loan]]:
        """Retrieve all currently active loans in the library."""
        try:
            loans = self._service.list_active_loans()
            return ControllerResult.ok(loans)
        except Exception as e:
            logger.exception("Error retrieving active loans")
            return ControllerResult.fail(f"Could not load active loans: {str(e)}")

    def get_member_loans(
        self,
        member_id: int,
        active_only: bool = False,
    ) -> ControllerResult[Sequence[Loan]]:
        """Retrieve borrowing history for a specific member."""
        try:
            loans = self._service.list_member_loans(member_id, active_only=active_only)
            return ControllerResult.ok(loans)
        except MemberNotFoundError as e:
            return ControllerResult.fail(str(e))
        except Exception as e:
            logger.exception("Error retrieving member loan history")
            return ControllerResult.fail(f"Could not load member loans: {str(e)}")

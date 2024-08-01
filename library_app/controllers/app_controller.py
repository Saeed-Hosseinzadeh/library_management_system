"""
Main application coordinator controller.

Acts as the central router and lifecycle manager, initializing underlying
services and making specific sub-controllers available to UI contexts.
"""

from __future__ import annotations

import logging

from library_app.controllers.book_controller import BookController
from library_app.controllers.loan_controller import LoanController
from library_app.controllers.member_controller import MemberController
from library_app.services.book_service import BookService
from library_app.services.loan_service import LoanService
from library_app.services.member_service import MemberService

logger = logging.getLogger(__name__)


class AppController:
    """Central coordinator for services and sub-controllers.

    Maintains instances of sub-controllers and provides a clean structural
    bridge between configuration/database startup and UI controllers.
    """

    def __init__(self) -> None:
        """Initialize core domain services and construct sub-controllers."""
        logger.info("Initializing application services...")

        # Instantiate Domain Services
        self._book_service = BookService()
        self._member_service = MemberService()
        self._loan_service = LoanService()

        # Instantiate Sub-Controllers
        self.books = BookController(self._book_service)
        self.members = MemberController(self._member_service)
        self.loans = LoanController(self._loan_service)

        logger.info("Application controller and sub-controllers initialized successfully.")

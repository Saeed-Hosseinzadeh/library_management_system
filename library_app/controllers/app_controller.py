from library_app.controllers.book_controller import BookController
from library_app.controllers.loan_controller import LoanController
from library_app.controllers.member_controller import MemberController


class AppController:
    """Centralized application controller."""

    def __init__(self):
        self.books = BookController()
        self.members = MemberController()
        self.loans = LoanController()

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from library_app.db.base import Base
from library_app.repositories.book_repository import BookRepository
from library_app.repositories.member_repository import MemberRepository
from library_app.repositories.loan_repository import LoanRepository
from library_app.services.book_service import BookService, BookCreateData
from library_app.services.member_service import MemberService, MemberCreateData
from library_app.services.loan_service import LoanService, BorrowBookData
from library_app.domain.exceptions import DuplicateISBNError, BookAlreadyLoanedError


class TestServiceLayer(unittest.TestCase):
    def setUp(self):
        # راه اندازی پایگاه داده موقت در حافظه برای تست‌های ایزوله
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()

        # مقداردهی اولیه ریپازیتوری‌ها و سرویس‌ها
        self.book_repo = BookRepository()
        self.member_repo = MemberRepository()
        self.loan_repo = LoanRepository()

        self.book_service = BookService(self.book_repo)
        self.member_service = MemberService(self.member_repo)
        self.loan_service = LoanService(self.loan_repo, self.book_repo, self.member_repo)

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_add_book_and_register_member_successfully(self):
        # Arrange
        book_data = BookCreateData(
            title="Clean Code", author="Robert C. Martin", isbn="9780132350884",
            publisher="Prentice Hall", category="Software", publication_year=2008,
            copies_total=5, quantity=5
        )
        member_data = MemberCreateData(
            member_id="M101", name="Saeed", phone="09171234567",
            national_id="2281234567", address="Sadra"
        )

        # Act
        book = self.book_service.add(self.session, book_data)
        member = self.member_service.add(self.session, member_data)
        self.session.flush()

        # Assert
        self.assertIsNotNone(book.id)
        self.assertIsNotNone(member.id)
        self.assertEqual(book.title, "Clean Code")
        self.assertEqual(member.member_id, "M101")

    def test_add_book_raises_duplicate_isbn_error(self):
        # Arrange
        book_data1 = BookCreateData(
            title="First Book", author="Author", isbn="9780132350884",
            copies_total=2, quantity=2
        )
        book_data2 = BookCreateData(
            title="Second Book", author="Author 2", isbn="9780132350884",
            copies_total=1, quantity=1
        )

        self.book_service.add(self.session, book_data1)
        self.session.flush()

        # Act & Assert
        with self.assertRaises(DuplicateISBNError):
            self.book_service.add(self.session, book_data2)

    def test_borrow_book_success_and_prevent_double_borrow(self):
        # Arrange
        book_data = BookCreateData(
            title="Clean Code", author="Robert C. Martin", isbn="9780132350884",
            copies_total=2, quantity=2
        )
        member_data = MemberCreateData(
            member_id="M101", name="Saeed", phone="09171234567",
            national_id="2281234567", address="Sadra"
        )

        self.book_service.add(self.session, book_data)
        self.member_service.add(self.session, member_data)
        self.session.flush()

        # Act 1: ثبت اولین امانت باید با موفقیت انجام شود
        borrow_dto = BorrowBookData(member_id="M101", isbn="9780132350884")
        loan = self.loan_service.issue_loan(self.session, borrow_dto)
        self.session.flush()

        self.assertIsNotNone(loan.id)

        # بررسی کاهش خودکار موجودی کتاب در دیتابیس
        updated_book = self.book_repo.get_by_isbn(self.session, "9780132350884")
        self.assertEqual(updated_book.quantity, 1)

        # Act 2: تلاش مجدد برای امانت گرفتن همان کتاب توسط همان عضو فعال باید خطا دهد
        with self.assertRaises(BookAlreadyLoanedError):
            self.loan_service.issue_loan(self.session, borrow_dto)

    def test_return_book_successfully_updates_return_date(self):
        # Arrange
        book_data = BookCreateData(
            title="Clean Code", author="Robert C. Martin", isbn="9780132350884",
            copies_total=1, quantity=1
        )
        member_data = MemberCreateData(
            member_id="M101", name="Saeed", phone="09171234567",
            national_id="2281234567", address="Sadra"
        )

        self.book_service.add(self.session, book_data)
        self.member_service.add(self.session, member_data)
        self.session.flush()

        borrow_dto = BorrowBookData(member_id="M101", isbn="9780132350884")
        loan = self.loan_service.issue_loan(self.session, borrow_dto)
        self.session.flush()

        # Act: بازگرداندن کتاب (اتمام امانت)
        returned_loan = self.loan_service.terminate_loan(self.session, loan.id)
        self.session.flush()

        # Assert: بررسی ثبت تاریخ بازگشت و افزایش مجدد موجودی کتاب
        self.assertIsNotNone(returned_loan.return_date)

        updated_book = self.book_repo.get_by_isbn(self.session, "9780132350884")
        self.assertEqual(updated_book.quantity, 1)


if __name__ == "__main__":
    unittest.main()
"""
Unit tests for domain validation functions.

This module validates that the utility functions under `library_app/domain/validators.py`
correctly normalize valid input and reject invalid input by raising ValidationError.
"""

from __future__ import annotations

import unittest

from library_app.domain.exceptions import ValidationError
from library_app.domain.validators import (
    sanitize_string,
    validate_non_empty_string,
    normalize_isbn,
    validate_isbn,
    normalize_iran_phone_number,
    validate_optional_iran_phone_number,
    validate_identifier,
)


class TestValidators(unittest.TestCase):
    """Test suite verifying string, ISBN, phone, and ID validations."""

    def test_sanitize_string_valid(self) -> None:
        """Ensure spaces are trimmed and multiple whitespace characters collapsed."""
        self.assertEqual(sanitize_string("  hello   world  "), "hello world")
        self.assertEqual(sanitize_string("\n  tabs\t and newlines\r "), "tabs and newlines")

    def test_sanitize_string_invalid_type(self) -> None:
        """Ensure sanitize_string raises ValidationError on non-string inputs."""
        with self.assertRaises(ValidationError):
            sanitize_string(12345)  # type: ignore

    def test_validate_non_empty_string_valid(self) -> None:
        """Verify valid string limits and sanitization are respected."""
        self.assertEqual(validate_non_empty_string(" Python ", "field", min_length=2), "Python")
        self.assertEqual(validate_non_empty_string("A", "field", min_length=1, max_length=1), "A")

    def test_validate_non_empty_string_too_short(self) -> None:
        """Ensure error is raised if string length falls below min_length."""
        with self.assertRaises(ValidationError):
            validate_non_empty_string("   ", "test_field", min_length=1)

    def test_validate_non_empty_string_too_long(self) -> None:
        """Ensure error is raised if string length exceeds max_length."""
        with self.assertRaises(ValidationError):
            validate_non_empty_string("long_text", "test_field", max_length=4)

    def test_normalize_isbn(self) -> None:
        """Ensure ISBN symbols are stripped and checksum characters are standardized."""
        self.assertEqual(normalize_isbn(" 978-3-16-148410-0 "), "9783161484100")
        self.assertEqual(normalize_isbn("0-306-40615-x"), "030640615X")

    def test_validate_isbn_10_valid(self) -> None:
        """Ensure valid ISBN-10 values pass verification."""
        # Valid ISBN-10 numbers with correct checksums
        self.assertEqual(validate_isbn("0-306-40615-2"), "0306406152")
        self.assertEqual(validate_isbn("0-393-04002-X"), "039304002X")

    def test_validate_isbn_13_valid(self) -> None:
        """Ensure valid ISBN-13 values pass verification."""
        # Valid ISBN-13 number
        self.assertEqual(validate_isbn("978-3-16-148410-0"), "9783161484100")

    def test_validate_isbn_invalid(self) -> None:
        """Ensure invalid ISBN checksums or formats are rejected."""
        with self.assertRaises(ValidationError):
            validate_isbn("0-306-40615-5")  # Invalid ISBN-10 checksum
        with self.assertRaises(ValidationError):
            validate_isbn("978-3-16-148410-9")  # Invalid ISBN-13 checksum
        with self.assertRaises(ValidationError):
            validate_isbn("not-an-isbn")

    def test_normalize_iran_phone_number_formats(self) -> None:
        """Ensure various Iranian mobile formats normalize to canonical 09xxxxxxxxx."""
        formats = ["09123456789", "9123456789", "+989123456789", "00989123456789"]
        for number in formats:
            with self.subTest(number=number):
                self.assertEqual(normalize_iran_phone_number(number), "09123456789")

    def test_normalize_iran_phone_number_invalid(self) -> None:
        """Ensure invalid mobile formats raise ValidationError."""
        invalid_numbers = ["0912345678", "08123456789", "+988123456789", "not-a-phone"]
        for number in invalid_numbers:
            with self.subTest(number=number):
                with self.assertRaises(ValidationError):
                    normalize_iran_phone_number(number)

    def test_validate_optional_iran_phone_number(self) -> None:
        """Verify optional phone rules resolve correctly to None or normalized values."""
        self.assertIsNone(validate_optional_iran_phone_number(None))
        self.assertIsNone(validate_optional_iran_phone_number("  "))
        self.assertEqual(validate_optional_iran_phone_number("09123456789"), "09123456789")

    def test_validate_identifier_valid(self) -> None:
        """Ensure clean identifiers with alphanumeric/hyphen/underscore pass."""
        self.assertEqual(validate_identifier("lib_member-01", "member_id"), "lib_member-01")

    def test_validate_identifier_invalid(self) -> None:
        """Ensure identifiers with forbidden special characters raise ValidationError."""
        invalid_ids = ["lib member", "member@01", "member#01"]
        for val in invalid_ids:
            with self.subTest(val=val):
                with self.assertRaises(ValidationError):
                    validate_identifier(val, "member_id")


if __name__ == "__main__":
    unittest.main()

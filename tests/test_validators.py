import unittest
from library_app.domain.validators import validate_isbn, validate_identifier
from library_app.domain.exceptions import ValidationError

class TestValidators(unittest.TestCase):
    def test_validate_isbn13_correct(self):
        # Clean Code ISBN-13 format
        result = validate_isbn("978-0132350884")
        self.assertEqual(result, "9780132350884")

    def test_validate_isbn10_correct(self):
        # Valid ISBN-10 format with 'X' checksum
        result = validate_isbn("0-8044-2957-X")
        self.assertEqual(result, "080442957X")

    def test_validate_isbn_invalid_raises_error(self):
        with self.assertRaises(ValidationError):
            validate_isbn("invalid-isbn-string")
        with self.assertRaises(ValidationError):
            validate_isbn("12345")

    def test_validate_identifier_correct(self):
        result = validate_identifier("M101-A_user", "Member ID")
        self.assertEqual(result, "M101-A_user")

    def test_validate_identifier_empty_raises_error(self):
        with self.assertRaises(ValidationError):
            validate_identifier("   ", "Member ID")

    def test_validate_identifier_invalid_chars_raises_error(self):
        with self.assertRaises(ValidationError):
            validate_identifier("M101@User!", "Member ID")

if __name__ == "__main__":
    unittest.main()
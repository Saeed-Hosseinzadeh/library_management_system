"""
Reusable validation and sanitization helpers for the Library Management System.

This module contains pure utility functions for validating and normalizing
common domain fields such as names, ISBN values, phone numbers, and
identifier-like strings.

Validation failures raise `ValidationError` from the domain layer.
"""

from __future__ import annotations

import re
from typing import Optional

from library_app.domain.exceptions import ValidationError


ISBN_10_PATTERN = re.compile(r"^\d{9}[\dXx]$")
ISBN_13_PATTERN = re.compile(r"^\d{13}$")
IRAN_PHONE_PATTERN = re.compile(r"^(?:\+98|0098|98|0)?9\d{9}$")


def sanitize_string(value: str, field_name: str = "value") -> str:
    """Trim and normalize whitespace in a string.

    Consecutive whitespace characters are collapsed into a single space.

    Args:
        value: The input string to sanitize.
        field_name: Human-readable field name for error messages.

    Returns:
        A trimmed and normalized string.

    Raises:
        ValidationError: If the provided value is not a string.
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    normalized = " ".join(value.strip().split())
    return normalized


def validate_non_empty_string(
    value: str,
    field_name: str,
    min_length: int = 1,
    max_length: Optional[int] = None,
) -> str:
    """Validate and normalize a non-empty string field.

    Args:
        value: The input string.
        field_name: Human-readable field name for error messages.
        min_length: Minimum allowed length after sanitization.
        max_length: Optional maximum allowed length after sanitization.

    Returns:
        The sanitized string.

    Raises:
        ValidationError: If the string is empty or violates length rules.
    """
    normalized = sanitize_string(value=value, field_name=field_name)

    if len(normalized) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} character(s) long."
        )

    if max_length is not None and len(normalized) > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} character(s) long."
        )

    return normalized


def normalize_isbn(value: str) -> str:
    """Normalize an ISBN by removing separators and uppercasing X.

    This function removes spaces and hyphens, then converts any trailing
    ISBN-10 check digit `x` to uppercase `X`.

    Args:
        value: Raw ISBN input.

    Returns:
        A normalized ISBN string.

    Raises:
        ValidationError: If the input is not a valid string.
    """
    normalized = sanitize_string(value, field_name="ISBN")
    normalized = normalized.replace("-", "").replace(" ", "").upper()
    return normalized


def _is_valid_isbn10(isbn: str) -> bool:
    """Validate an ISBN-10 using checksum rules.

    Args:
        isbn: A normalized ISBN-10 string.

    Returns:
        True if valid, otherwise False.
    """
    if not ISBN_10_PATTERN.fullmatch(isbn):
        return False

    total = 0
    for index, char in enumerate(isbn[:9], start=1):
        total += index * int(char)

    check_char = isbn[9]
    check_value = 10 if check_char == "X" else int(check_char)
    total += 10 * check_value

    return total % 11 == 0


def _is_valid_isbn13(isbn: str) -> bool:
    """Validate an ISBN-13 using checksum rules.

    Args:
        isbn: A normalized ISBN-13 string.

    Returns:
        True if valid, otherwise False.
    """
    if not ISBN_13_PATTERN.fullmatch(isbn):
        return False

    total = 0
    for index, char in enumerate(isbn[:12]):
        digit = int(char)
        total += digit if index % 2 == 0 else digit * 3

    expected_check_digit = (10 - (total % 10)) % 10
    actual_check_digit = int(isbn[12])

    return expected_check_digit == actual_check_digit


def validate_isbn(value: str) -> str:
    """Validate an ISBN-10 or ISBN-13 value.

    The function accepts values containing spaces or hyphens and returns
    the normalized ISBN string if valid.

    Args:
        value: Raw ISBN input.

    Returns:
        The normalized valid ISBN.

    Raises:
        ValidationError: If the ISBN is invalid.
    """
    isbn = normalize_isbn(value)

    if _is_valid_isbn10(isbn) or _is_valid_isbn13(isbn):
        return isbn

    raise ValidationError("ISBN must be a valid ISBN-10 or ISBN-13 value.")


def normalize_iran_phone_number(value: str) -> str:
    """Normalize an Iranian mobile phone number to canonical format.

    Supported input examples:
        - 09123456789
        - 989123456789
        - +989123456789
        - 00989123456789

    Output canonical format:
        - 09123456789

    Args:
        value: Raw phone number input.

    Returns:
        A normalized Iranian mobile number in `09xxxxxxxxx` format.

    Raises:
        ValidationError: If the number is invalid.
    """
    normalized = sanitize_string(value, field_name="phone number")
    normalized = normalized.replace(" ", "").replace("-", "")

    if not IRAN_PHONE_PATTERN.fullmatch(normalized):
        raise ValidationError("Phone number must be a valid Iranian mobile number.")

    if normalized.startswith("+98"):
        return "0" + normalized[3:]
    if normalized.startswith("0098"):
        return "0" + normalized[4:]
    if normalized.startswith("98"):
        return "0" + normalized[2:]
    if normalized.startswith("9"):
        return "0" + normalized

    return normalized


def validate_optional_iran_phone_number(value: Optional[str]) -> Optional[str]:
    """Validate an optional Iranian mobile phone number.

    Args:
        value: Raw optional phone number input.

    Returns:
        A normalized phone number, or `None` if the input is empty.

    Raises:
        ValidationError: If a non-empty value is invalid.
    """
    if value is None:
        return None

    if isinstance(value, str) and not value.strip():
        return None

    return normalize_iran_phone_number(value)


def validate_identifier(
    value: str,
    field_name: str,
    max_length: int = 50,
) -> str:
    """Validate a generic identifier such as member ID or librarian ID.

    This helper trims whitespace and enforces a conservative set of
    allowed characters.

    Allowed characters:
        - letters
        - digits
        - underscore
        - hyphen

    Args:
        value: Raw identifier input.
        field_name: Human-readable field name.
        max_length: Maximum allowed identifier length.

    Returns:
        The normalized identifier.

    Raises:
        ValidationError: If the identifier is empty or contains
            unsupported characters.
    """
    normalized = validate_non_empty_string(
        value=value,
        field_name=field_name,
        min_length=1,
        max_length=max_length,
    )

    if not re.fullmatch(r"[A-Za-z0-9_-]+", normalized):
        raise ValidationError(
            f"{field_name} may only contain letters, digits, underscores, and hyphens."
        )

    return normalized

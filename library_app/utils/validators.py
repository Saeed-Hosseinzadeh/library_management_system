"""Validation and normalization utilities.

This module provides reusable validation helpers for the Library Management System.
"""

from __future__ import annotations

import re
from typing import Optional

from library_app.domain.exceptions import ValidationError

_WHITESPACE_RE = re.compile(r"\s+")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_ISBN_10_RE = re.compile(r"^\d{9}[\dX]$")
_ISBN_13_RE = re.compile(r"^\d{13}$")
_NON_DIGIT_RE = re.compile(r"\D+")


def sanitize_string(value: str) -> str:
    """Trim a string and collapse internal whitespace."""
    if not isinstance(value, str):
        raise ValidationError("Expected a string value.")
    return _WHITESPACE_RE.sub(" ", value).strip()


def validate_non_empty_string(
    value: str,
    field_name: str = "Value",
    min_length: int = 1,
    max_length: Optional[int] = None,
) -> str:
    """Validate that a string is not empty after sanitization.

    Note: field_name and min_length are regular positional arguments to match tests.
    """
    cleaned = sanitize_string(value)

    if not cleaned:
        raise ValidationError(f"{field_name} must not be empty.")

    if len(cleaned) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long.")

    if max_length is not None and len(cleaned) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters long.")

    return cleaned


def validate_identifier(
        value: str,
        field_name: str = "Identifier",
        max_length: Optional[int] = None
) -> str:
    """Validate a compact identifier containing letters, digits, _ and -.

    Accepts max_length to safely accommodate service-layer assertions.
    """
    cleaned = validate_non_empty_string(value, field_name, min_length=1, max_length=max_length)

    if " " in cleaned:
        raise ValidationError(f"{field_name} must not contain spaces.")

    if not _IDENTIFIER_RE.fullmatch(cleaned):
        raise ValidationError(
            f"{field_name} may only contain letters, digits, underscores, and hyphens."
        )

    return cleaned


def normalize_isbn(value: str) -> str:
    """Normalize an ISBN by removing spaces/hyphens and uppercasing X."""
    if not isinstance(value, str):
        raise ValidationError("ISBN must be a string.")

    cleaned = value.replace("-", "").replace(" ", "").strip().upper()

    if not cleaned:
        raise ValidationError("ISBN must not be empty.")

    return cleaned


def _is_valid_isbn10(isbn: str) -> bool:
    if not _ISBN_10_RE.fullmatch(isbn):
        return False

    total = 0
    for index, char in enumerate(isbn[:9], start=1):
        total += index * int(char)

    check_char = isbn[9]
    check_value = 10 if check_char == "X" else int(check_char)
    total += 10 * check_value

    return total % 11 == 0


def _is_valid_isbn13(isbn: str) -> bool:
    if not _ISBN_13_RE.fullmatch(isbn):
        return False

    total = 0
    for index, char in enumerate(isbn[:12]):
        digit = int(char)
        total += digit if index % 2 == 0 else digit * 3

    expected_check = (10 - (total % 10)) % 10
    return expected_check == int(isbn[12])


def validate_isbn(value: str) -> str:
    """Validate and return a normalized ISBN-10 or ISBN-13."""
    isbn = normalize_isbn(value)

    if len(isbn) == 10:
        if not _is_valid_isbn10(isbn):
            raise ValidationError("Invalid ISBN-10 checksum.")
        return isbn

    if len(isbn) == 13:
        if not _is_valid_isbn13(isbn):
            raise ValidationError("Invalid ISBN-13 checksum.")
        return isbn

    raise ValidationError("ISBN must be either 10 or 13 characters long.")


def normalize_iran_mobile(value: str) -> str:
    """Normalize Iranian mobile numbers to local format: 09123456789."""
    if not isinstance(value, str):
        raise ValidationError("Phone number must be a string.")

    raw = sanitize_string(value)
    digits = _NON_DIGIT_RE.sub("", raw)

    if not digits:
        raise ValidationError("Phone number must not be empty.")

    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98"):
        digits = digits[2:]

    if not digits.startswith("0"):
        digits = f"0{digits}"

    if not re.fullmatch(r"09\d{9}", digits):
        raise ValidationError(
            "Invalid Iranian mobile number. Expected format similar to 09123456789."
        )

    return digits


def validate_optional_iran_mobile(value: Optional[str]) -> Optional[str]:
    """Validate an optional Iranian mobile number."""
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValidationError("Phone number must be a string or None.")

    if not sanitize_string(value):
        return None

    return normalize_iran_mobile(value)


# ---------------------------------------------------------------------------
# Compatibility aliases required by tests
# ---------------------------------------------------------------------------
def normalize_iran_phone_number(value: str) -> str:
    return normalize_iran_mobile(value)


def validate_optional_iran_phone_number(value: Optional[str]) -> Optional[str]:
    return validate_optional_iran_mobile(value)
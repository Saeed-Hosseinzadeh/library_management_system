import re

from library_app.domain.exceptions import ValidationError

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_NON_DIGIT_PATTERN = re.compile(r"\D")


def sanitize_string(value: str) -> str:
    """Strip string value."""
    return value.strip()


def validate_non_empty_string(value: str, field_name: str) -> str:
    """Validate a required string."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")
    cleaned = sanitize_string(value)
    if not cleaned:
        raise ValidationError(f"{field_name} cannot be empty.")
    return cleaned


def validate_identifier(value: str, field_name: str = "Identifier") -> str:
    """Validate an identifier."""
    cleaned = validate_non_empty_string(value, field_name)
    if not _IDENTIFIER_PATTERN.fullmatch(cleaned):
        raise ValidationError(
            f"{field_name} must contain only letters, numbers, hyphens, or underscores."
        )
    return cleaned


def normalize_isbn(isbn: str) -> str:
    """Normalize ISBN."""
    cleaned = validate_non_empty_string(isbn, "ISBN").upper()
    return _NON_DIGIT_PATTERN.sub("", cleaned[:-1]) + cleaned[-1] if cleaned.endswith("X") else _NON_DIGIT_PATTERN.sub("", cleaned)


def _is_valid_isbn10(isbn: str) -> bool:
    """Validate ISBN-10 checksum."""
    if len(isbn) != 10:
        return False

    total = 0
    for index, char in enumerate(isbn[:9], start=1):
        if not char.isdigit():
            return False
        total += index * int(char)

    check_char = isbn[-1]
    if check_char == "X":
        total += 10 * 10
    elif check_char.isdigit():
        total += 10 * int(check_char)
    else:
        return False

    return total % 11 == 0


def _is_valid_isbn13(isbn: str) -> bool:
    """Validate ISBN-13 checksum."""
    if len(isbn) != 13 or not isbn.isdigit():
        return False

    total = 0
    for index, char in enumerate(isbn[:12]):
        factor = 1 if index % 2 == 0 else 3
        total += int(char) * factor

    check_digit = (10 - (total % 10)) % 10
    return check_digit == int(isbn[-1])


def validate_isbn(isbn: str) -> str:
    """Validate and normalize ISBN."""
    normalized = normalize_isbn(isbn)
    if len(normalized) == 10 and _is_valid_isbn10(normalized):
        return normalized
    if len(normalized) == 13 and _is_valid_isbn13(normalized):
        return normalized
    raise ValidationError("ISBN is invalid.")

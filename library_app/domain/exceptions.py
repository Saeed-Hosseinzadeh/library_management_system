"""
Custom domain and business exceptions for the Library Management System.

These exceptions provide a clean and explicit way to express business
rule failures, lookup issues, and validation-related domain errors.

The service layer should raise these exceptions instead of generic
built-in exceptions whenever possible.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain-specific exceptions."""


class ValidationError(DomainError):
    """Raised when domain validation fails."""


class NotFoundError(DomainError):
    """Raised when a requested entity cannot be found."""


class ConflictError(DomainError):
    """Raised when an operation violates a uniqueness or state constraint."""


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""


class BookNotFoundError(NotFoundError):
    """Raised when a book cannot be found."""


class MagazineNotFoundError(NotFoundError):
    """Raised when a magazine cannot be found."""


class MemberNotFoundError(NotFoundError):
    """Raised when a member cannot be found."""


class LibrarianNotFoundError(NotFoundError):
    """Raised when a librarian cannot be found."""


class LoanNotFoundError(NotFoundError):
    """Raised when a loan record cannot be found."""


class DuplicateISBNError(ConflictError):
    """Raised when an ISBN already exists in the system."""


class DuplicateMemberIDError(ConflictError):
    """Raised when a member ID already exists in the system."""


class DuplicateLibrarianIDError(ConflictError):
    """Raised when a librarian ID already exists in the system."""


class BookAlreadyLoanedError(BusinessRuleError):
    """Raised when attempting to loan a book that is already loaned out."""


class OutOfStockError(BusinessRuleError):
    """Raised when an item cannot be loaned because it is unavailable."""


class InvalidReturnError(BusinessRuleError):
    """Raised when a return operation is invalid or inconsistent."""


class UnauthorizedOperationError(BusinessRuleError):
    """Raised when an action is not permitted by system rules."""

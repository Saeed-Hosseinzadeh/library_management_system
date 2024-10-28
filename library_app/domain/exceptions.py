class LibraryException(Exception):
    """Base library exception."""


class ValidationError(LibraryException):
    """Validation failure."""


class NotFoundError(LibraryException):
    """Entity not found."""


class ConflictError(LibraryException):
    """Conflict error."""


class BusinessRuleError(LibraryException):
    """Business rule violation."""


class BookNotFoundError(NotFoundError):
    """Book not found."""


class MemberNotFoundError(NotFoundError):
    """Member not found."""


class LoanNotFoundError(NotFoundError):
    """Loan not found."""


class DuplicateISBNError(ConflictError):
    """Duplicate ISBN."""


class DuplicateMemberIDError(ConflictError):
    """Duplicate member ID."""


class OutOfStockError(BusinessRuleError):
    """Book out of stock."""


class BookAlreadyLoanedError(BusinessRuleError):
    """Duplicate active loan."""


class InvalidReturnError(BusinessRuleError):
    """Invalid return state."""

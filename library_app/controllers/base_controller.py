from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class ControllerResult(Generic[T]):
    """Represents the outcome of a controller operation."""

    success: bool
    data: Optional[T] = None
    message: Optional[str] = None

    @classmethod
    def ok(
        cls,
        data: Optional[T] = None,
        message: Optional[str] = None,
    ) -> "ControllerResult[T]":
        """Create a successful result."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, message: str) -> "ControllerResult[T]":
        """Create a failed result."""
        return cls(success=False, data=None, message=message)

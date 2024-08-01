"""
Base controller components.

Provides the common result contract used by all controllers to communicate
execution status, payloads, and errors back to the UI layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(slots=True, frozen=True)
class ControllerResult(Generic[T]):
    """Unified response object returned by controllers to the UI layer.

    Attributes:
        success: True if the operation succeeded, False otherwise.
        data: Optional payload containing domain objects or serializable data.
        message: UI-friendly status message or error details.
    """

    success: bool
    data: Optional[T] = None
    message: str = ""

    @classmethod
    def ok(cls, data: Optional[T] = None, message: str = "") -> ControllerResult[T]:
        """Create a successful result."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, message: str) -> ControllerResult[T]:
        """Create a failed result containing a UI-friendly error message."""
        return cls(success=False, data=None, message=message)

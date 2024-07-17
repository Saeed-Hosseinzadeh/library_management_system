"""
Business service for managing library members.

This module encapsulates member registration, updates, and lookup
workflows. It validates input, coordinates repository access, and
raises explicit domain exceptions for controller-level handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from library_app.db.models import Member
from library_app.db.session import session_scope
from library_app.domain.exceptions import (
    DuplicateMemberIDError,
    MemberNotFoundError,
)
from library_app.domain.validators import (
    normalize_iran_phone_number,
    validate_identifier,
    validate_non_empty_string,
    validate_optional_iran_phone_number,
)
from library_app.repositories.member_repository import MemberRepository


@dataclass(slots=True, frozen=True)
class MemberCreateData:
    """Input data required to register a new member.

    Attributes:
        name: Member full name.
        member_id: Business-level unique member identifier.
        phone: Optional Iranian mobile number.
        address: Optional address text.
    """

    name: str
    member_id: str
    phone: Optional[str] = None
    address: Optional[str] = None


@dataclass(slots=True, frozen=True)
class MemberUpdateData:
    """Input data for partial member profile updates.

    Attributes:
        name: Updated full name.
        phone: Updated phone number. Empty string is treated as clearing
            the optional value.
        address: Updated address text.
    """

    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class MemberService:
    """Service layer for member business operations."""

    def register_member(self, data: MemberCreateData) -> Member:
        """Register a new library member.

        The service validates the incoming profile, ensures the member ID
        is unique, and persists the new entity in a single transaction.

        Args:
            data: Structured member registration payload.

        Returns:
            The newly created persistent Member entity.

        Raises:
            DuplicateMemberIDError: If the member_id already exists.
        """
        name = validate_non_empty_string(
            value=data.name,
            field_name="name",
            min_length=1,
            max_length=255,
        )
        member_id = validate_identifier(
            value=data.member_id,
            field_name="member_id",
            max_length=50,
        )
        phone = validate_optional_iran_phone_number(data.phone)

        address = None
        if data.address is not None and data.address.strip():
            address = validate_non_empty_string(
                value=data.address,
                field_name="address",
                min_length=1,
                max_length=500,
            )

        with session_scope() as session:
            repository = MemberRepository(session)

            existing = repository.get_by_member_uid(member_id)
            if existing is not None:
                raise DuplicateMemberIDError(
                    f"A member with ID '{member_id}' already exists."
                )

            member = Member(
                name=name,
                member_id=member_id,
                phone=phone,
                address=address,
            )
            repository.create(member)
            session.flush()
            session.refresh(member)
            return member

    def get_member_by_id(self, member_db_id: int) -> Member:
        """Retrieve a member by database primary key.

        Args:
            member_db_id: Integer primary key.

        Returns:
            The matching Member entity.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        with session_scope() as session:
            repository = MemberRepository(session)
            member = repository.get_by_id(member_db_id)
            if member is None:
                raise MemberNotFoundError(
                    f"Member with id '{member_db_id}' was not found."
                )
            return member

    def get_member_by_member_id(self, member_id: str) -> Member:
        """Retrieve a member by business-level member ID.

        Args:
            member_id: Raw or normalized member identifier.

        Returns:
            The matching Member entity.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        normalized_member_id = validate_identifier(
            value=member_id,
            field_name="member_id",
            max_length=50,
        )

        with session_scope() as session:
            repository = MemberRepository(session)
            member = repository.get_by_member_uid(normalized_member_id)
            if member is None:
                raise MemberNotFoundError(
                    f"Member with member_id '{normalized_member_id}' was not found."
                )
            return member

    def list_members(self) -> list[Member]:
        """Return all registered members.

        Returns:
            A list of Member entities.
        """
        with session_scope() as session:
            repository = MemberRepository(session)
            return list(repository.get_all())

    def search_members(self, query: str) -> list[Member]:
        """Search members by name.

        Args:
            query: User-provided search term.

        Returns:
            A list of matching members.
        """
        normalized_query = validate_non_empty_string(
            value=query,
            field_name="query",
            min_length=1,
            max_length=255,
        )

        with session_scope() as session:
            repository = MemberRepository(session)
            return list(repository.search_by_name(normalized_query))

    def update_member(self, member_db_id: int, data: MemberUpdateData) -> Member:
        """Update a member profile.

        Args:
            member_db_id: Database primary key of the member.
            data: Partial update payload.

        Returns:
            The updated Member entity.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        with session_scope() as session:
            repository = MemberRepository(session)
            member = repository.get_by_id(member_db_id)
            if member is None:
                raise MemberNotFoundError(
                    f"Member with id '{member_db_id}' was not found."
                )

            if data.name is not None:
                member.name = validate_non_empty_string(
                    value=data.name,
                    field_name="name",
                    min_length=1,
                    max_length=255,
                )

            if data.phone is not None:
                member.phone = validate_optional_iran_phone_number(data.phone)

            if data.address is not None:
                member.address = (
                    validate_non_empty_string(
                        value=data.address,
                        field_name="address",
                        min_length=1,
                        max_length=500,
                    )
                    if data.address.strip()
                    else None
                )

            session.flush()
            session.refresh(member)
            return member

    def delete_member(self, member_db_id: int) -> None:
        """Delete a member by database primary key.

        Args:
            member_db_id: Primary key of the member.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        with session_scope() as session:
            repository = MemberRepository(session)
            member = repository.get_by_id(member_db_id)
            if member is None:
                raise MemberNotFoundError(
                    f"Member with id '{member_db_id}' was not found."
                )
            repository.delete(member)

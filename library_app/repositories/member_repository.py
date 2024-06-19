"""
Repository implementation for Member data access.

This module provides data access patterns for the Member entity using
SQLAlchemy 2.0 style queries.
"""

from __future__ import annotations

from typing import Sequence, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from library_app.db.models import Member


class MemberRepository:
    """Manages database operations for the Member entity."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session: An active SQLAlchemy Session.
        """
        self._session = session

    def create(self, member: Member) -> Member:
        """Persist a new Member entity in the database.

        Args:
            member: The Member transient instance to save.

        Returns:
            The persisted Member entity with its primary key populated.
        """
        self._session.add(member)
        return member

    def get_by_id(self, member_id: int) -> Optional[Member]:
        """Retrieve a Member by its primary key (integer database ID).

        Args:
            member_id: The primary key of the member.

        Returns:
            The Member entity if found, otherwise None.
        """
        return self._session.get(Member, member_id)

    def get_by_member_uid(self, member_uid: str) -> Optional[Member]:
        """Retrieve a Member by their business key (e.g., custom member string ID).

        Args:
            member_uid: The custom unique identifier string for the member.

        Returns:
            The Member entity if found, otherwise None.
        """
        stmt = select(Member).where(Member.member_id == member_uid)
        return self._session.scalars(stmt).first()

    def get_all(self) -> Sequence[Member]:
        """Retrieve all Member entities from the database.

        Returns:
            A sequence containing all Members.
        """
        stmt = select(Member).order_by(Member.name)
        return self._session.scalars(stmt).all()

    def search_by_name(self, query: str) -> Sequence[Member]:
        """Search members containing a query string in their name.

        Args:
            query: The substring search keyword.

        Returns:
            A sequence of matching Member entities.
        """
        pattern = f"%{query}%"
        stmt = select(Member).where(Member.name.like(pattern)).order_by(Member.name)
        return self._session.scalars(stmt).all()

    def delete(self, member: Member) -> None:
        """Remove a Member entity from the database.

        Args:
            member: The persistent Member entity to delete.
        """
        self._session.delete(member)

    def delete_by_id(self, member_id: int) -> bool:
        """Remove a Member by its database primary key.

        Args:
            member_id: The database primary key of the member to delete.

        Returns:
            True if the member was found and deleted, False otherwise.
        """
        member = self.get_by_id(member_id)
        if member:
            self.delete(member)
            return True
        return False

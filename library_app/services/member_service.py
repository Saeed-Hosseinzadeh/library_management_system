from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from library_app.db.models import Member
from library_app.domain.exceptions import DuplicateMemberIDError, MemberNotFoundError, ValidationError
from library_app.domain.validators import validate_identifier, validate_non_empty_string
from library_app.repositories.member_repository import MemberRepository


@dataclass(slots=True)
class MemberCreateData:
    """Member creation payload."""

    member_id: str
    name: str
    phone: str | None = None
    national_id: str | None = None
    address: str | None = None


@dataclass(slots=True)
class MemberUpdateData:
    """Member update payload."""

    member_id: str
    name: str
    phone: str | None = None
    national_id: str | None = None
    address: str | None = None


class MemberService:
    """Member business logic."""

    def __init__(self, repository: MemberRepository | None = None) -> None:
        self.repository = repository or MemberRepository()

    def list(self, session: Session) -> Sequence[Member]:
        """Return all members."""
        statement = select(Member).order_by(Member.name.asc(), Member.id.asc())
        return session.execute(statement).scalars().all()

    def search(self, session: Session, query: str) -> Sequence[Member]:
        """Search members."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return self.list(session)
        return self.repository.search(session, cleaned_query)

    def add(self, session: Session, data: MemberCreateData) -> Member:
        """Create a new member."""
        member_id = validate_identifier(data.member_id, "member_id")
        name = validate_non_empty_string(data.name, "name")
        phone = self._clean_optional(data.phone)
        national_id = self._clean_optional(data.national_id)
        address = self._clean_optional(data.address)

        if self.repository.get_by_member_id(session, member_id):
            raise DuplicateMemberIDError("A member with this member_id already exists.")

        member = Member(
            member_id=member_id,
            name=name,
            phone=phone,
            national_id=national_id,
            address=address,
        )
        return self.repository.add(session, member)

    def update(self, session: Session, member_pk: int, data: MemberUpdateData) -> Member:
        """Update an existing member."""
        member = self.repository.get_by_id(session, member_pk)
        if member is None:
            raise MemberNotFoundError("Member not found.")

        member_id = validate_identifier(data.member_id, "member_id")
        name = validate_non_empty_string(data.name, "name")
        phone = self._clean_optional(data.phone)
        national_id = self._clean_optional(data.national_id)
        address = self._clean_optional(data.address)

        existing = self.repository.get_by_member_id(session, member_id)
        if existing is not None and existing.id != member.id:
            raise DuplicateMemberIDError("A member with this member_id already exists.")

        member.member_id = member_id
        member.name = name
        member.phone = phone
        member.national_id = national_id
        member.address = address

        session.flush()
        return member

    def remove(self, session: Session, member_pk: int) -> None:
        """Delete a member."""
        member = self.repository.get_by_id(session, member_pk)
        if member is None:
            raise MemberNotFoundError("Member not found.")
        self.repository.delete(session, member)

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        """Normalize optional text fields."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

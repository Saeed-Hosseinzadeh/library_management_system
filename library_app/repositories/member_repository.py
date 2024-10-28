from __future__ import annotations

from typing import Sequence

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from library_app.db.models import Member


class MemberRepository:
    """Persistence operations for members."""

    def get_by_id(self, session: Session, id: int) -> Member | None:
        """Return a member by primary key."""
        return session.get(Member, id)

    def get_by_member_id(self, session: Session, member_id: str) -> Member | None:
        """Return a member by business identifier."""
        statement = select(Member).where(Member.member_id == member_id)
        return session.execute(statement).scalar_one_or_none()

    def search(self, session: Session, query: str) -> Sequence[Member]:
        """Search members by member ID, name, phone, national ID, or address."""
        term = f"%{query.strip()}%"
        statement = (
            select(Member)
            .where(
                or_(
                    Member.member_id.ilike(term),
                    Member.name.ilike(term),
                    Member.phone.ilike(term),
                    Member.national_id.ilike(term),
                    Member.address.ilike(term),
                )
            )
            .order_by(Member.name.asc(), Member.id.asc())
        )
        return session.execute(statement).scalars().all()

    def add(self, session: Session, member: Member) -> Member:
        """Add a member to the session."""
        session.add(member)
        session.flush()
        return member

    def delete(self, session: Session, member: Member) -> None:
        """Delete a member from the session."""
        session.delete(member)
        session.flush()

from __future__ import annotations

import logging
from typing import Sequence

from library_app.controllers.base_controller import ControllerResult
from library_app.db.models import Member
from library_app.db.session import session_scope
from library_app.domain.exceptions import DuplicateMemberIDError, MemberNotFoundError, ValidationError
from library_app.services.member_service import MemberCreateData, MemberService, MemberUpdateData

logger = logging.getLogger(__name__)


class MemberController:
    """Member controller."""

    def __init__(self, service: MemberService | None = None) -> None:
        self.service = service or MemberService()

    def list_members(self) -> ControllerResult[Sequence[Member]]:
        """Return all members."""
        try:
            with session_scope() as session:
                members = self.service.list(session)
                return ControllerResult.ok(members)
        except Exception:
            logger.exception("Failed to list members.")
            return ControllerResult.fail("Failed to list members.")

    def search_members(self, query: str) -> ControllerResult[Sequence[Member]]:
        """Search members."""
        try:
            with session_scope() as session:
                members = self.service.search(session, query)
                return ControllerResult.ok(members)
        except Exception:
            logger.exception("Failed to search members.")
            return ControllerResult.fail("Failed to search members.")

    def add_member(
        self,
        member_id: str,
        name: str,
        phone: str | None = None,
        national_id: str | None = None,
        address: str | None = None,
    ) -> ControllerResult[Member]:
        """Create a member."""
        try:
            payload = MemberCreateData(
                member_id=member_id,
                name=name,
                phone=phone,
                national_id=national_id,
                address=address,
            )
            with session_scope() as session:
                member = self.service.add(session, payload)
                return ControllerResult.ok(member, "Member created successfully.")
        except (ValidationError, DuplicateMemberIDError) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to add member.")
            return ControllerResult.fail("Failed to add member.")

    def update_member(
        self,
        member_pk: int,
        member_id: str,
        name: str,
        phone: str | None = None,
        national_id: str | None = None,
        address: str | None = None,
    ) -> ControllerResult[Member]:
        """Update a member."""
        try:
            payload = MemberUpdateData(
                member_id=member_id,
                name=name,
                phone=phone,
                national_id=national_id,
                address=address,
            )
            with session_scope() as session:
                member = self.service.update(session, member_pk, payload)
                return ControllerResult.ok(member, "Member updated successfully.")
        except (ValidationError, DuplicateMemberIDError, MemberNotFoundError) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to update member.")
            return ControllerResult.fail("Failed to update member.")

    def remove_member(self, member_pk: int) -> ControllerResult[None]:
        """Delete a member."""
        try:
            with session_scope() as session:
                self.service.remove(session, member_pk)
                return ControllerResult.ok(message="Member removed successfully.")
        except (ValidationError, MemberNotFoundError) as exc:
            return ControllerResult.fail(str(exc))
        except Exception:
            logger.exception("Failed to remove member.")
            return ControllerResult.fail("Failed to remove member.")

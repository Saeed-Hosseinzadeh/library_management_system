"""
Controller for handling member-related UI requests.
"""

from __future__ import annotations

import logging
from typing import Sequence

from library_app.controllers.base_controller import ControllerResult
from library_app.db.models import Member
from library_app.domain.exceptions import (
    DuplicateMemberIDError,
    MemberNotFoundError,
)
from library_app.services.member_service import (
    MemberCreateData,
    MemberService,
    MemberUpdateData,
)

logger = logging.getLogger(__name__)


class MemberController:
    """Coordinates UI requests for members with the MemberService."""

    def __init__(self, member_service: MemberService) -> None:
        """Initialize the controller with its backing service."""
        self._service = member_service

    def register_member(
        self,
        name: str,
        member_id: str,
        phone: str = "",
        address: str = "",
    ) -> ControllerResult[Member]:
        """Validate input parameters and register a new library member."""
        try:
            data = MemberCreateData(
                name=name,
                member_id=member_id,
                phone=phone.strip() or None,
                address=address.strip() or None,
            )
            member = self._service.register_member(data)
            return ControllerResult.ok(member, f"Member '{member.name}' registered successfully.")

        except DuplicateMemberIDError as e:
            return ControllerResult.fail(str(e))
        except ValueError as e:
            return ControllerResult.fail(f"Validation error: {str(e)}")
        except Exception as e:
            logger.exception("Error registering member")
            return ControllerResult.fail(f"An unexpected error occurred: {str(e)}")

    def get_all_members(self) -> ControllerResult[Sequence[Member]]:
        """Retrieve all registered members."""
        try:
            members = self._service.list_members()
            return ControllerResult.ok(members)
        except Exception as e:
            logger.exception("Failed to retrieve members")
            return ControllerResult.fail(f"Could not retrieve member list: {str(e)}")

    def search_members(self, query: str) -> ControllerResult[Sequence[Member]]:
        """Search members by name matching the query."""
        if not query.strip():
            return self.get_all_members()
        try:
            results = self._service.search_members(query)
            return ControllerResult.ok(results)
        except ValueError as e:
            return ControllerResult.fail(f"Search parameter error: {str(e)}")
        except Exception as e:
            logger.exception("Member search failed")
            return ControllerResult.fail(f"An error occurred while searching: {str(e)}")

    def update_member(
        self,
        member_db_id: int,
        name: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> ControllerResult[Member]:
        """Modify profile attributes of a member."""
        try:
            data = MemberUpdateData(
                name=name,
                phone=phone,
                address=address,
            )
            updated_member = self._service.update_member(member_db_id, data)
            return ControllerResult.ok(updated_member, "Member profile updated successfully.")

        except MemberNotFoundError as e:
            return ControllerResult.fail(str(e))
        except ValueError as e:
            return ControllerResult.fail(f"Validation error: {str(e)}")
        except Exception as e:
            logger.exception("Error updating member profile")
            return ControllerResult.fail(f"Update failed: {str(e)}")

    def delete_member(self, member_db_id: int) -> ControllerResult[None]:
        """Deregister a member from the system."""
        try:
            self._service.delete_member(member_db_id)
            return ControllerResult.ok(message="Member deleted successfully.")
        except MemberNotFoundError as e:
            return ControllerResult.fail(str(e))
        except Exception as e:
            logger.exception("Error deleting member")
            return ControllerResult.fail(f"Deletion failed: {str(e)}")

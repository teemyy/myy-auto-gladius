from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.team import Team
    from ..systems.economy import EconomySystem, ShopListing


class AIDecisionPriority:
    """Ordered list of spending priorities for AI teams."""
    FILL_EMPTY_SLOT  = 1   # recruit if roster has open slots
    UPGRADE_WEAPON   = 2   # buy a better weapon for weakest-armed gladiator
    UPGRADE_ARMOR    = 3   # buy a better armor for weakest-armored gladiator
    RECRUIT_EXTRA    = 4   # recruit even if roster is not empty (if gold allows)


class AITeamManager:
    """Controls an AI-managed team between tournaments.

    Each AI team follows a simple scripted decision tree:
    1. Fill empty roster slots first.
    2. Upgrade the weapon of the gladiator with the lowest attack.
    3. Upgrade the armor of the gladiator with the lowest defense.
    4. Recruit an additional gladiator if budget allows.

    No lookahead or probabilistic planning — keep it deterministic and cheap.
    """

    def __init__(self, team: "Team"):
        self.team: "Team" = team

    # ------------------------------------------------------------------

    def take_turn(self, economy: "EconomySystem") -> None:
        """Execute the AI's full between-tournament spending turn.

        Called once per tournament intermission for each AI team.
        Internally calls the priority methods in order until gold runs out.
        """
        pass

    # ------------------------------------------------------------------
    # Decision steps
    # ------------------------------------------------------------------

    def _fill_empty_slots(self, economy: "EconomySystem") -> bool:
        """Buy recruits until the roster is full or gold runs out.

        Returns True if at least one gladiator was recruited.
        """
        pass

    def _upgrade_weapons(self, economy: "EconomySystem") -> bool:
        """Buy a better weapon for the gladiator with the lowest effective attack.

        Returns True if a purchase was made.
        """
        pass

    def _upgrade_armors(self, economy: "EconomySystem") -> bool:
        """Buy better armor for the gladiator with the lowest effective defense.

        Returns True if a purchase was made.
        """
        pass

    def _recruit_extra(self, economy: "EconomySystem") -> bool:
        """Recruit one additional gladiator if funds allow and roster has room.

        Returns True if a gladiator was recruited.
        """
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _best_affordable(
        self,
        listings: list["ShopListing"],
        budget: int,
    ) -> "ShopListing | None":
        """Return the highest-value affordable listing within budget."""
        pass

    def _gladiator_needs_weapon(self) -> bool:
        """Return True if any roster gladiator has no weapon equipped."""
        pass

    def _gladiator_needs_armor(self) -> bool:
        """Return True if any roster gladiator has no armor equipped."""
        pass

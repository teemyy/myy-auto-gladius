from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.team import Team
    from ..systems.economy import EconomySystem


class ManagementScreen:
    """Between-tournament management screen for the player's team.

    Tabs:
        "roster"   -- view and inspect gladiators; equip/unequip items
        "shop"     -- buy weapons, armor, or recruit new gladiators
        "sell"     -- sell equipped items back for gold

    The screen returns control to the game when the player presses the
    "Ready" button (or equivalent key), signalling readiness for the next match.
    """

    TABS = ("roster", "shop", "sell")

    def __init__(
        self,
        surface:  pygame.Surface,
        team:     "Team",
        economy:  "EconomySystem",
    ):
        self.surface  = surface
        self.team     = team
        self.economy  = economy
        self.active_tab:      str            = "roster"
        self.selected_index:  int            = 0   # selected item in the active list
        self._done:           bool           = False

    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Update any animations or timed UI elements."""
        pass

    def draw(self) -> None:
        """Render the full management screen for the current tab."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route keyboard/mouse events to the active tab handler."""
        pass

    def is_done(self) -> bool:
        """Return True when the player has confirmed they are ready to fight."""
        pass

    # ------------------------------------------------------------------
    # Tab renderers
    # ------------------------------------------------------------------

    def _draw_roster_tab(self) -> None:
        """Render the gladiator roster with stats, equipment, and status."""
        pass

    def _draw_shop_tab(self) -> None:
        """Render the shop inventory with item stats and buy buttons."""
        pass

    def _draw_sell_tab(self) -> None:
        """Render equipped items available to sell with sell-price labels."""
        pass

    # ------------------------------------------------------------------
    # Input handlers
    # ------------------------------------------------------------------

    def _handle_roster_input(self, event: pygame.event.Event) -> None:
        """Handle item selection and equip/unequip actions on the roster tab."""
        pass

    def _handle_shop_input(self, event: pygame.event.Event) -> None:
        """Handle item selection and purchase confirmation on the shop tab."""
        pass

    def _handle_sell_input(self, event: pygame.event.Event) -> None:
        """Handle item selection and sell confirmation on the sell tab."""
        pass

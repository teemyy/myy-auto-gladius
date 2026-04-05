from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.team import Team
    from ..systems.tournament import Tournament


class BracketScreen:
    """Tournament overview screen showing the schedule and current standings.

    Panels:
        "schedule"   -- full round-robin fixture list with results filled in
        "standings"  -- league table sorted by win rate / gold tiebreaker
        "details"    -- expanded view of a selected match or team roster

    Transitions to the arena screen when the player selects an upcoming match
    (the player's team's next fight).
    """

    PANELS = ("schedule", "standings", "details")

    def __init__(
        self,
        surface:    pygame.Surface,
        tournament: "Tournament",
        player_team: "Team",
    ):
        self.surface      = surface
        self.tournament   = tournament
        self.player_team  = player_team
        self.active_panel: str  = "standings"
        self.selected_row: int  = 0
        self._done:        bool = False

    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Update any scroll animations or highlights."""
        pass

    def draw(self) -> None:
        """Render the full bracket screen for the active panel."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Navigate rows, switch panels, or confirm a match selection."""
        pass

    def is_done(self) -> bool:
        """Return True when the player has chosen to proceed to a match."""
        pass

    # ------------------------------------------------------------------
    # Panel renderers
    # ------------------------------------------------------------------

    def _draw_schedule_panel(self) -> None:
        """Render all fixtures; highlight played matches and upcoming ones."""
        pass

    def _draw_standings_panel(self) -> None:
        """Render the sorted league table with win rate and gold columns."""
        pass

    def _draw_details_panel(self) -> None:
        """Render the expanded view for the currently selected match or team."""
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _next_player_match(self):
        """Return the next unplayed match involving the player's team, or None."""
        pass

    def _highlight_row(self, y: int, width: int, height: int) -> None:
        """Draw a selection highlight rectangle behind the given row."""
        pass

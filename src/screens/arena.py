from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..entities.enemy  import Enemy
    from ..systems.combat  import CombatResolver, RoundResult


class ArenaScreen:
    """Turn-based battle screen.

    States:
        "player_choose"  -- waiting for the player to pick an action
        "resolving"      -- brief pause while the round result is displayed
        "round_log"      -- scrolling the round's log lines before next input
        "battle_over"    -- win or loss banner; wait for input to continue
    """

    ACTION_KEYS = {
        pygame.K_1: "Heavy",
        pygame.K_2: "Quick",
        pygame.K_3: "Defend",
        pygame.K_4: "Ranged",
    }

    def __init__(
        self,
        surface:  pygame.Surface,
        player:   "Player",
        enemy:    "Enemy",
        resolver: "CombatResolver",
    ):
        self.surface   = surface
        self.player    = player
        self.enemy     = enemy
        self.resolver  = resolver
        self.state:    str                    = "player_choose"
        self.last_result: "RoundResult | None" = None
        self.log_lines: list[str]             = []
        self._done:    bool                   = False
        self._victory: bool                   = False

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Advance any timed states (e.g. auto-advance from resolving after a pause)."""
        pass

    def draw(self) -> None:
        """Render the full arena screen for the current state."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route input: action selection keys during player_choose, SPACE to advance log."""
        pass

    def is_done(self) -> bool:
        """Return True when the battle is over and the screen should close."""
        pass

    def player_won(self) -> bool:
        """Return True if the player was the winner."""
        pass

    # ── Drawing helpers ──────────────────────────────────────────────────────

    def _draw_combatant_panel(self, entity, rect: pygame.Rect, flip: bool = False) -> None:
        """Draw HP bar, stamina bar, limb integrity grid, and name for one combatant."""
        pass

    def _draw_action_menu(self) -> None:
        """Render the 1–4 action choice prompt during player_choose state."""
        pass

    def _draw_round_log(self) -> None:
        """Display the log lines from the last resolved round."""
        pass

    def _draw_battle_over_banner(self) -> None:
        """Render the victory or defeat overlay."""
        pass

    # ── Round handling ───────────────────────────────────────────────────────

    def _execute_round(self, player_action: str) -> None:
        """Ask the enemy for its action, call resolver.resolve_round(), update state."""
        pass

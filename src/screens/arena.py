from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.team import Team
    from ..systems.combat import CombatSystem, BattleResult


class ArenaScreen:
    """Animated arena screen that plays back a live auto-battle.

    Receives two teams and a CombatSystem, then steps the simulation each
    frame while rendering gladiator sprites, health bars, projectiles, and
    passive effect indicators.

    States:
        "intro"    -- brief pause before battle starts
        "battle"   -- simulation running
        "outro"    -- result banner, waiting for player input to continue
    """

    def __init__(
        self,
        surface: pygame.Surface,
        team_a:  "Team",
        team_b:  "Team",
        combat:  "CombatSystem",
    ):
        self.surface  = surface
        self.team_a   = team_a
        self.team_b   = team_b
        self.combat   = combat
        self.state:   str                  = "intro"
        self.result:  "BattleResult | None" = None
        self._intro_timer: float           = 0.0

        self.sprites:     pygame.sprite.Group = pygame.sprite.Group()
        self.projectiles: pygame.sprite.Group = pygame.sprite.Group()

    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance the screen state each frame."""
        pass

    def draw(self) -> None:
        """Render the arena, combatants, projectiles, HUD, and overlays."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle keyboard/mouse input (e.g. SPACE to continue from outro)."""
        pass

    def is_done(self) -> bool:
        """Return True when the screen is finished and the game should move on."""
        pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _draw_arena_floor(self) -> None:
        """Draw the dark arena background and border."""
        pass

    def _draw_combatants(self) -> None:
        """Blit all gladiator sprites and their HP bars."""
        pass

    def _draw_hud(self) -> None:
        """Draw team names, team HP totals, and current match info."""
        pass

    def _draw_result_overlay(self) -> None:
        """Draw the victory/defeat banner over the arena."""
        pass

    def _sync_sprites_to_combat(self) -> None:
        """Update sprite positions from CombatantState positions each frame."""
        pass

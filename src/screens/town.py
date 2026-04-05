from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.player    import Player
    from ..systems.equipment  import EquipmentSystem


class TownLocation:
    """Named town hub locations."""
    SMITHY   = "smithy"
    STORE    = "store"
    TRAINING = "training"
    HEALER   = "healer"
    GATE     = "gate"        # exit town and proceed to next stage


class TownScreen:
    """Town hub screen shown between every stage.

    The player can visit four locations before committing to the next fight.
    Pressing ENTER / clicking the Gate exits town and advances to the arena.

    Sub-screens (Smithy, Store, Training, Healer) are rendered inline;
    TownScreen owns all their state rather than spawning new screen objects.

    States:
        "main"      -- hub overview, choose a location
        "smithy"    -- weapon buy/sell/upgrade UI
        "store"     -- armor buy/sell UI
        "training"  -- spend gold for +1 agility
        "healer"    -- select limbs to restore; shows cost per limb
    """

    LOCATION_KEYS = {
        pygame.K_1: TownLocation.SMITHY,
        pygame.K_2: TownLocation.STORE,
        pygame.K_3: TownLocation.TRAINING,
        pygame.K_4: TownLocation.HEALER,
        pygame.K_5: TownLocation.GATE,
    }

    def __init__(
        self,
        surface:   pygame.Surface,
        player:    "Player",
        equipment: "EquipmentSystem",
        stage:     int,
    ):
        self.surface   = surface
        self.player    = player
        self.equipment = equipment
        self.stage     = stage
        self.state:    str  = "main"
        self._done:    bool = False
        self._shop_weapons: list[dict] = []
        self._shop_armors:  list[dict] = []
        self._selected_idx: int        = 0

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Update any animated elements."""
        pass

    def draw(self) -> None:
        """Render the active sub-screen."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Route keyboard input to the active sub-screen handler."""
        pass

    def is_done(self) -> bool:
        """Return True once the player leaves through the Gate."""
        pass

    # ── Sub-screen renderers ─────────────────────────────────────────────────

    def _draw_main_hub(self) -> None:
        """Render the hub overview with gold balance and location menu."""
        pass

    def _draw_smithy(self) -> None:
        """Render weapon shop: current weapon, available stock, upgrade option."""
        pass

    def _draw_store(self) -> None:
        """Render armor shop: current armor, available stock."""
        pass

    def _draw_training(self) -> None:
        """Render training prompt: current agility, cost, confirm button."""
        pass

    def _draw_healer(self) -> None:
        """Render healer: limb integrity table with cost and restore buttons."""
        pass

    # ── Sub-screen input handlers ────────────────────────────────────────────

    def _handle_smithy_input(self, event: pygame.event.Event) -> None:
        """Buy, sell, or upgrade weapons; navigate with arrow keys."""
        pass

    def _handle_store_input(self, event: pygame.event.Event) -> None:
        """Buy or sell armor."""
        pass

    def _handle_training_input(self, event: pygame.event.Event) -> None:
        """Confirm agility training if player has enough gold."""
        pass

    def _handle_healer_input(self, event: pygame.event.Event) -> None:
        """Select limb, confirm restore, deduct gold."""
        pass

    # ── Town shop helpers ────────────────────────────────────────────────────

    def _refresh_shop_stock(self) -> None:
        """Populate _shop_weapons and _shop_armors based on current stage."""
        pass

    def _healer_cost(self, limb: str, current_integrity: int) -> int:
        """Return the gold cost to fully restore a limb (scales with damage)."""
        pass

    def _training_cost(self, current_agility: int) -> int:
        """Return the gold cost for the next +1 agility point."""
        pass

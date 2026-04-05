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
        "training"  -- invest gold in STR, AGI, or END (permanent)
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
        pass

    def draw(self) -> None:
        if self.state == "main":
            self._draw_main_hub()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if self.state == "main":
            loc = self.LOCATION_KEYS.get(event.key)
            if loc == TownLocation.GATE or event.key == pygame.K_RETURN:
                self._done = True
            elif loc in (TownLocation.SMITHY, TownLocation.STORE,
                         TownLocation.TRAINING, TownLocation.HEALER):
                pass   # sub-locations not yet implemented

    def is_done(self) -> bool:
        return self._done

    def get_result(self) -> str:
        return "proceed"

    # ── Sub-screen renderers ─────────────────────────────────────────────────

    def _draw_main_hub(self) -> None:
        from ..settings import (SCREEN_WIDTH, SCREEN_HEIGHT, DARK_BG,
                                GOLD_TEXT, WHITE, GRAY, PANEL_BG, DARK_GRAY)

        surface = self.surface
        surface.fill(DARK_BG)

        font_title  = pygame.font.SysFont(None, 72)
        font_sub    = pygame.font.SysFont(None, 34)
        font_body   = pygame.font.SysFont(None, 30)
        font_hint   = pygame.font.SysFont(None, 26)
        W, H        = SCREEN_WIDTH, SCREEN_HEIGHT

        # ── Title bar ──────────────────────────────────────────────────────
        pygame.draw.rect(surface, (22, 16, 10), (0, 0, W, 72))
        pygame.draw.line(surface, (70, 52, 22), (0, 72), (W, 72), 2)

        title = font_title.render("TOWN HUB", True, GOLD_TEXT)
        surface.blit(title, title.get_rect(centerx=W // 2, centery=36))

        stage_surf = font_sub.render(f"Stage {self.stage}", True, (155, 125, 55))
        surface.blit(stage_surf, (W - 160, 24))

        # ── Player info panel ──────────────────────────────────────────────
        info_rect = pygame.Rect(40, 100, 340, 160)
        pygame.draw.rect(surface, PANEL_BG, info_rect, border_radius=6)
        pygame.draw.rect(surface, (55, 42, 22), info_rect, 1, border_radius=6)

        name_surf = font_sub.render(self.player.name, True, WHITE)
        surface.blit(name_surf, (info_rect.x + 18, info_rect.y + 18))

        gold_label = font_body.render("Gold", True, GRAY)
        gold_val   = font_sub.render(str(self.player.gold), True, GOLD_TEXT)
        surface.blit(gold_label, (info_rect.x + 18, info_rect.y + 62))
        surface.blit(gold_val,   (info_rect.x + 80, info_rect.y + 58))

        hp_label = font_body.render(f"HP  {self.player.hp} / {self.player.max_hp}", True, (180, 80, 80))
        surface.blit(hp_label, (info_rect.x + 18, info_rect.y + 102))

        str_label = font_body.render(f"STR  {self.player.strength}", True, (200,  95,  50))
        agi_label = font_body.render(f"AGI  {self.player.agility}", True, (200, 175,  55))
        end_label = font_body.render(f"END  {self.player.endurance}", True, ( 55, 185, 165))
        surface.blit(str_label, (info_rect.x + 18,  info_rect.y + 128))
        surface.blit(agi_label, (info_rect.x + 120, info_rect.y + 128))
        surface.blit(end_label, (info_rect.x + 18,  info_rect.y + 150))

        # ── Location menu ──────────────────────────────────────────────────
        locations = [
            ("1", "Smithy",          "(coming soon)", (160, 130, 60)),
            ("2", "Store",           "(coming soon)", (160, 130, 60)),
            ("3", "Training Ground", "Invest gold → +1 STR / AGI / END  (coming soon)", (160, 130, 60)),
            ("4", "Healer",          "(coming soon)", (160, 130, 60)),
            ("5", "Gate",            "→ Proceed to Stage " + str(self.stage), ( 80, 200,  80)),
        ]

        menu_rect = pygame.Rect(440, 100, 780, 500)
        pygame.draw.rect(surface, PANEL_BG, menu_rect, border_radius=6)
        pygame.draw.rect(surface, (55, 42, 22), menu_rect, 1, border_radius=6)

        header = font_sub.render("Where would you like to go?", True, (155, 125, 55))
        surface.blit(header, (menu_rect.x + 20, menu_rect.y + 20))
        pygame.draw.line(surface, (55, 42, 22),
                         (menu_rect.x + 10, menu_rect.y + 58),
                         (menu_rect.right - 10, menu_rect.y + 58), 1)

        for i, (key, name, desc, color) in enumerate(locations):
            row_y    = menu_rect.y + 76 + i * 72
            row_rect = pygame.Rect(menu_rect.x + 12, row_y, menu_rect.w - 24, 60)
            bg       = (32, 24, 14) if name == "Gate" else (24, 18, 12)
            pygame.draw.rect(surface, bg, row_rect, border_radius=4)

            key_surf  = font_sub.render(f"[{key}]", True, GOLD_TEXT)
            name_surf = font_sub.render(name, True, color)
            desc_surf = font_body.render(desc, True, GRAY)

            surface.blit(key_surf,  (row_rect.x + 14, row_rect.y + 8))
            surface.blit(name_surf, (row_rect.x + 68, row_rect.y + 8))
            surface.blit(desc_surf, (row_rect.x + 68, row_rect.y + 36))

        # ── Hint ───────────────────────────────────────────────────────────
        hint = font_hint.render("[1–4] Visit location     [5] / [ENTER] Proceed to next stage",
                                True, (65, 55, 40))
        surface.blit(hint, hint.get_rect(center=(W // 2, H - 22)))

    def _draw_smithy(self) -> None:
        """Render weapon shop: current weapon, available stock, upgrade option."""
        pass

    def _draw_store(self) -> None:
        """Render armor shop: current armor, available stock."""
        pass

    def _draw_training(self) -> None:
        """Render training menu: choose STR, AGI, or END; show current value and gold cost."""
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
        """Select stat (STR/AGI/END) and confirm training if player has enough gold."""
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

    def _training_cost(self, stat: str, current_value: int) -> int:
        """Return the gold cost for the next +1 point in the given stat (STR/AGI/END).

        Cost scales with current_value so repeated investment gets more expensive.
        """
        pass

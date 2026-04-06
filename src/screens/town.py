from __future__ import annotations
import os
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.player   import Player
    from ..systems.equipment import EquipmentSystem

_W, _H  = 1280, 720
_ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images")

_GOLD   = (220, 175,  60)
_WHITE  = (255, 255, 255)
_GRAY   = (130, 120, 100)
_DARK   = ( 12,   9,   6)
_PANEL  = ( 22,  16,  10)
_BORDER = ( 70,  52,  22)
_GREEN  = ( 80, 200,  80)
_HOVER  = (255, 230, 120)

# (id, display label, button-center x, button-center y on the 1280×720 background)
_BTN_W, _BTN_H = 170, 50
_BUILDINGS: list[tuple[str, str, int, int]] = [
    ("smithy",   "Smithy",          312, 195),
    ("store",    "General Store",   318, 502),
    ("training", "Training",        898, 472),
    ("gate",     "Enter Arena →",   912, 155),
    ("healer",   "Healer",          640, 658),
]
_SUB_LABELS = {
    "smithy":   "Smithy",
    "store":    "General Store",
    "training": "Training Ground",
    "healer":   "Healer",
}


class TownScreen:
    """Town hub screen shown between every stage.

    States: "main" | "smithy" | "store" | "training" | "healer"
    """

    def __init__(
        self,
        surface:   pygame.Surface,
        player:    "Player",
        equipment: "EquipmentSystem | None",
        stage:     int,
    ):
        self.surface   = surface
        self.player    = player
        self.equipment = equipment
        self.stage     = stage
        self.state     = "main"
        self._done     = False
        self._hover: str | None = None

        self._fa = pygame.font.SysFont(None, 52)
        self._fb = pygame.font.SysFont(None, 34)
        self._fc = pygame.font.SysFont(None, 26)

        # Background image
        self._bg: pygame.Surface | None = None
        try:
            raw = pygame.image.load(os.path.join(_ASSETS, "town_bg_1.webp")).convert()
            self._bg = pygame.transform.smoothscale(raw, (_W, _H))
        except (pygame.error, FileNotFoundError):
            pass

        # Pre-compute button rects from center positions
        self._btn_rects: dict[str, pygame.Rect] = {
            bid: pygame.Rect(cx - _BTN_W // 2, cy - _BTN_H // 2, _BTN_W, _BTN_H)
            for bid, _, cx, cy in _BUILDINGS
        }
        self._back_rect: pygame.Rect | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        self._draw_main()
        if self.state != "main":
            self._draw_sub_overlay()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self._hover = next(
                (bid for bid, rect in self._btn_rects.items()
                 if rect.collidepoint(pos) and self.state == "main"),
                None,
            )

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "main":
                for bid, rect in self._btn_rects.items():
                    if rect.collidepoint(pos):
                        if bid == "gate":
                            self._done = True
                        else:
                            self.state = bid
                        return
            else:
                if self._back_rect and self._back_rect.collidepoint(pos):
                    self.state = "main"

        elif event.type == pygame.KEYDOWN:
            if self.state != "main" and event.key == pygame.K_ESCAPE:
                self.state = "main"
            elif self.state == "main" and event.key in (pygame.K_RETURN,):
                self._done = True

    def is_done(self) -> bool:
        return self._done

    def get_result(self) -> str:
        return "proceed"

    # ── Drawing ──────────────────────────────────────────────────────────────

    def _draw_main(self) -> None:
        if self._bg:
            self.surface.blit(self._bg, (0, 0))
        else:
            self.surface.fill(_DARK)

        # Player info overlay — top-left corner
        info = pygame.Surface((230, 72), pygame.SRCALPHA)
        info.fill((10, 7, 4, 210))
        self.surface.blit(info, (8, 8))
        self.surface.blit(self._fb.render(self.player.name, True, _WHITE), (16, 12))
        self.surface.blit(
            self._fc.render(f"HP  {self.player.hp}/{self.player.max_hp}", True, (200, 80, 80)),
            (16, 44),
        )
        self.surface.blit(
            self._fc.render(f"Gold  {self.player.gold}", True, _GOLD),
            (130, 44),
        )

        # Stage label — top-right corner
        s = self._fb.render(f"Stage {self.stage}", True, _GOLD)
        self.surface.blit(s, s.get_rect(right=_W - 14, top=12))

        # Building buttons
        for bid, label, *_ in _BUILDINGS:
            rect    = self._btn_rects[bid]
            hovered = (self._hover == bid and self.state == "main")
            is_gate = (bid == "gate")

            bg_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg_surf.fill((80, 200, 80, 200) if is_gate else (14, 10, 6, 210))
            self.surface.blit(bg_surf, rect.topleft)

            bd_col  = _HOVER if hovered else (_GREEN  if is_gate else _BORDER)
            txt_col = _HOVER if hovered else (_GREEN  if is_gate else _GOLD)
            pygame.draw.rect(self.surface, bd_col, rect, 2, border_radius=5)

            lbl = self._fb.render(label, True, txt_col)
            self.surface.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_sub_overlay(self) -> None:
        # Dim the background
        dim = pygame.Surface((_W, _H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        self.surface.blit(dim, (0, 0))

        # Central panel
        panel = pygame.Rect(_W // 2 - 320, _H // 2 - 240, 640, 480)
        pygame.draw.rect(self.surface, _PANEL, panel, border_radius=8)
        pygame.draw.rect(self.surface, _BORDER, panel, 2, border_radius=8)

        title_txt = _SUB_LABELS.get(self.state, self.state.title())
        title     = self._fa.render(title_txt, True, _GOLD)
        self.surface.blit(title, title.get_rect(centerx=panel.centerx, top=panel.top + 24))
        pygame.draw.line(self.surface, _BORDER,
                         (panel.x + 20, panel.top + 82),
                         (panel.right - 20, panel.top + 82), 1)

        # Placeholder content
        cs = self._fb.render("(Coming soon)", True, _GRAY)
        self.surface.blit(cs, cs.get_rect(center=(panel.centerx, panel.centery - 20)))

        # Back button
        back    = pygame.Rect(panel.centerx - 95, panel.bottom - 72, 190, 46)
        mouse   = pygame.mouse.get_pos()
        hovered = back.collidepoint(mouse)
        pygame.draw.rect(self.surface, (35, 26, 16), back, border_radius=6)
        pygame.draw.rect(self.surface, _HOVER if hovered else _BORDER, back, 2, border_radius=6)
        bl = self._fb.render("← Back to Town", True, _HOVER if hovered else _WHITE)
        self.surface.blit(bl, bl.get_rect(center=back.center))
        self._back_rect = back

from __future__ import annotations
import pygame
from ..settings import SCREEN_WIDTH, SCREEN_HEIGHT, DARK_BG, GOLD_TEXT, WHITE, GRAY

_ITEMS = ["Start", "Settings", "Quit"]


class MainMenuScreen:
    """Title screen with Start / Settings / Quit.

    Keyboard: UP/DOWN to navigate, ENTER/SPACE to confirm, ESC quits.
    Mouse:    hover selects, click confirms.

    get_result() returns "start" | "settings" | "quit" once is_done() is True.
    """

    def __init__(self, surface: pygame.Surface):
        self.surface  = surface
        self.selected = 0
        self._done    = False
        self._result: str | None = None

        self._font_title    = pygame.font.SysFont(None, 100)
        self._font_subtitle = pygame.font.SysFont(None, 38)
        self._font_item     = pygame.font.SysFont(None, 54)
        self._font_hint     = pygame.font.SysFont(None, 28)

        item_start_y = 340
        item_h       = 64
        item_gap     = 12
        self._item_rects = [
            pygame.Rect(SCREEN_WIDTH // 2 - 140, item_start_y + i * (item_h + item_gap),
                        280, item_h)
            for i in range(len(_ITEMS))
        ]

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        mx, my = pygame.mouse.get_pos()
        for i, rect in enumerate(self._item_rects):
            if rect.collidepoint(mx, my):
                self.selected = i

    def draw(self) -> None:
        self.surface.fill(DARK_BG)

        # Decorative horizontal rules
        rule_color = (55, 42, 22)
        pygame.draw.line(self.surface, rule_color, (0, 298), (SCREEN_WIDTH, 298), 1)
        pygame.draw.line(self.surface, rule_color, (0, 576), (SCREEN_WIDTH, 576), 1)

        # Title
        title = self._font_title.render("MYY AUTO GLADIUS", True, GOLD_TEXT)
        self.surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 160)))

        # Subtitle
        sub = self._font_subtitle.render("A Gladiator's Challenge", True, (155, 125, 55))
        self.surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 240)))

        # Menu items
        for i, (label, rect) in enumerate(zip(_ITEMS, self._item_rects)):
            active = i == self.selected
            if active:
                pygame.draw.rect(self.surface, (38, 28, 10), rect, border_radius=4)
                pygame.draw.rect(self.surface, GOLD_TEXT, rect, 1, border_radius=4)
                arrow = self._font_item.render("›", True, GOLD_TEXT)
                self.surface.blit(arrow, (rect.left - 28, rect.top + 10))

            color = GOLD_TEXT if active else GRAY
            text  = self._font_item.render(label, True, color)
            self.surface.blit(text, text.get_rect(center=rect.center))

        # Hint
        hint = self._font_hint.render("↑ ↓  navigate     ENTER  select", True, (65, 55, 40))
        self.surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 622)))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(_ITEMS)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(_ITEMS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._commit()
            elif event.key == pygame.K_ESCAPE:
                self._result = "quit"
                self._done   = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    self._commit()

    def is_done(self) -> bool:
        return self._done

    def get_result(self) -> str | None:
        return self._result

    # ── Internal ──────────────────────────────────────────────────────────────

    def _commit(self) -> None:
        self._result = _ITEMS[self.selected].lower()
        self._done   = True

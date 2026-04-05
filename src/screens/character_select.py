from __future__ import annotations
import math
import pygame
from ..settings import SCREEN_WIDTH, SCREEN_HEIGHT, DARK_BG, GOLD_TEXT, WHITE, GRAY, DARK_GRAY

# ── Character definitions ─────────────────────────────────────────────────────

CHARACTERS: list[dict] = [
    {
        "id":               "yumi",
        "name":             "Yumi",
        "title":            "The Swift Blade",
        "tagline":          "Speed is her only armor.",
        "hp":               100,
        "stamina":          120,
        "strength":           8,   # low STR — relies on crits and evasion
        "agility":           18,   # high AGI — frequent crits and dodges
        "starting_weapon":  "iron_sword",
        # Visuals
        "portrait_bg":      ( 28,  40,  80),
        "hair_color":       ( 48,  32, 105),
        "eye_color":        ( 70, 150, 220),
        "outfit_color":     ( 38,  65, 135),
        "accent_color":     ( 90, 145, 215),
        "hair_style":       "long",
        "card_border":      ( 80, 130, 220),
    },
    {
        "id":               "hana",
        "name":             "Hana",
        "title":            "The Iron Guard",
        "tagline":          "She has never taken a step back.",
        "hp":               140,
        "stamina":           90,
        "strength":          18,   # high STR — hits hard, shrugs off damage
        "agility":            6,   # low AGI — does not dodge or crit often
        "starting_weapon":  "iron_axe",
        # Visuals
        "portrait_bg":      ( 72,  22,  22),
        "hair_color":       ( 85,  48,  28),
        "eye_color":        (210,  75,  55),
        "outfit_color":     (105,  38,  32),
        "accent_color":     (200,  88,  58),
        "hair_style":       "short",
        "card_border":      (200,  75,  55),
    },
    {
        "id":               "rei",
        "name":             "Rei",
        "title":            "The Shadow",
        "tagline":          "She decides when battles end.",
        "hp":                90,
        "stamina":          110,
        "strength":          10,   # medium STR
        "agility":           20,   # highest AGI — master of evasion and crits
        "starting_weapon":  "iron_bow",
        # Visuals
        "portrait_bg":      ( 32,  18,  65),
        "hair_color":       ( 20,  12,  45),
        "eye_color":        (148,  88, 220),
        "outfit_color":     ( 55,  30,  95),
        "accent_color":     (140,  75, 215),
        "hair_style":       "twintail",
        "card_border":      (145,  80, 215),
    },
]

# Normalisation maxima for stat bars
_HP_MAX      = 150
_STAMINA_MAX = 130
_STR_MAX     = 20
_AGI_MAX     = 22

CARD_W      = 290
CARD_H      = 430
PORTRAIT_H  = 215
_GAP        = 35
_CARD_Y     = 118
_START_X    = (SCREEN_WIDTH - (3 * CARD_W + 2 * _GAP)) // 2


# ── Portrait drawing ──────────────────────────────────────────────────────────

def _draw_portrait(surface: pygame.Surface, rect: pygame.Rect, char: dict) -> None:
    """Draw a placeholder anime-girl portrait using pygame primitives."""
    pygame.draw.rect(surface, char["portrait_bg"], rect)

    hair   = char["hair_color"]
    outfit = char["outfit_color"]
    accent = char["accent_color"]
    eyes   = char["eye_color"]
    skin   = (222, 188, 162)
    cx     = rect.centerx
    top    = rect.top
    head_cy = top + 88      # centre of the face circle

    style = char["hair_style"]

    # ── Back hair ────────────────────────────────────────────────────────────
    if style == "long":
        pygame.draw.rect(surface, hair, (cx - 40, head_cy - 12, 22, 105))
        pygame.draw.rect(surface, hair, (cx + 18, head_cy - 12, 22, 105))
    elif style == "twintail":
        pts_l = [(cx-38, head_cy+8), (cx-20, head_cy+8),
                 (cx-18, head_cy+95), (cx-42, head_cy+90)]
        pts_r = [(cx+20, head_cy+8), (cx+38, head_cy+8),
                 (cx+42, head_cy+90), (cx+18, head_cy+95)]
        pygame.draw.polygon(surface, hair, pts_l)
        pygame.draw.polygon(surface, hair, pts_r)

    # Back-of-head ellipse
    pygame.draw.ellipse(surface, hair, (cx - 38, head_cy - 28, 76, 68))

    # ── Face ─────────────────────────────────────────────────────────────────
    pygame.draw.circle(surface, skin, (cx, head_cy + 5), 32)

    # ── Front hair / bangs ───────────────────────────────────────────────────
    pygame.draw.ellipse(surface, hair, (cx - 36, head_cy - 24, 72, 28))
    if style == "short":
        pygame.draw.ellipse(surface, hair, (cx - 46, head_cy - 8, 20, 32))
        pygame.draw.ellipse(surface, hair, (cx + 26, head_cy - 8, 20, 32))

    # ── Eyes ─────────────────────────────────────────────────────────────────
    for ex in (cx - 16, cx + 5):
        pygame.draw.ellipse(surface, eyes,         (ex, head_cy + 1, 12, 9))
        pygame.draw.ellipse(surface, (18, 12, 28), (ex + 1, head_cy + 2, 10, 7))
        pygame.draw.circle(surface, WHITE,         (ex + 3, head_cy + 1), 2)

    # ── Smile ─────────────────────────────────────────────────────────────────
    pygame.draw.arc(surface, (170, 115, 100),
                    pygame.Rect(cx - 7, head_cy + 18, 14, 8),
                    math.pi, 2 * math.pi, 2)

    # ── Body ─────────────────────────────────────────────────────────────────
    body_y = head_cy + 36
    pygame.draw.rect(surface, outfit, (cx - 30, body_y, 60, 78))
    pygame.draw.polygon(surface, accent,
                        [(cx, body_y + 4), (cx - 11, body_y + 26), (cx + 11, body_y + 26)])

    # Arms
    pygame.draw.rect(surface, outfit, (cx - 48, body_y + 6, 19, 55))
    pygame.draw.rect(surface, outfit, (cx + 29, body_y + 6, 19, 55))

    # Hands
    pygame.draw.circle(surface, skin, (cx - 39, body_y + 63), 8)
    pygame.draw.circle(surface, skin, (cx + 39, body_y + 63), 8)


# ── Screen ────────────────────────────────────────────────────────────────────

class CharacterSelectScreen:
    """Three-card character selection screen with a confirmation prompt.

    States:
        "selecting"   -- player browses cards with arrow keys or mouse
        "confirming"  -- overlay asks 'Start the challenge as [name]? Y/N'

    get_result() returns the selected character dict (confirmed) or None (back).
    """

    def __init__(self, surface: pygame.Surface):
        self.surface      = surface
        self.selected_idx = 0
        self._hover_idx   = -1
        self.state        = "selecting"
        self._done        = False
        self._result: dict | None = None

        self._card_rects = [
            pygame.Rect(_START_X + i * (CARD_W + _GAP), _CARD_Y, CARD_W, CARD_H)
            for i in range(3)
        ]

        self._font_title    = pygame.font.SysFont(None, 42)
        self._font_name     = pygame.font.SysFont(None, 48)
        self._font_subtitle = pygame.font.SysFont(None, 28)
        self._font_stat     = pygame.font.SysFont(None, 24)
        self._font_hint     = pygame.font.SysFont(None, 28)
        self._font_confirm  = pygame.font.SysFont(None, 52)
        self._font_confirm2 = pygame.font.SysFont(None, 36)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        mx, my = pygame.mouse.get_pos()
        self._hover_idx = -1
        for i, rect in enumerate(self._card_rects):
            if rect.collidepoint(mx, my):
                self._hover_idx = i

    def draw(self) -> None:
        self.surface.fill(DARK_BG)

        # Screen title
        title = self._font_title.render("SELECT YOUR GLADIATOR", True, GOLD_TEXT)
        self.surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 62)))
        pygame.draw.line(self.surface, (55, 42, 22),
                         (0, 92), (SCREEN_WIDTH, 92), 1)

        for i, (char, rect) in enumerate(zip(CHARACTERS, self._card_rects)):
            self._draw_card(i, char, rect)

        # Bottom hint
        hint = self._font_hint.render(
            "← →  browse     ENTER  select     ESC  back", True, (65, 55, 40))
        self.surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 688)))

        if self.state == "confirming":
            self._draw_confirmation(CHARACTERS[self.selected_idx])

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.state == "selecting":
            self._handle_selecting(event)
        else:
            self._handle_confirming(event)

    def is_done(self) -> bool:
        return self._done

    def get_result(self) -> dict | None:
        return self._result

    # ── Card drawing ──────────────────────────────────────────────────────────

    def _draw_card(self, idx: int, char: dict, rect: pygame.Rect) -> None:
        selected = idx == self.selected_idx
        hovered  = idx == self._hover_idx

        # Card background
        bg = (28, 22, 18) if not selected else (38, 30, 20)
        pygame.draw.rect(self.surface, bg, rect, border_radius=6)

        # Border
        border_color = char["card_border"] if selected else (55, 45, 35)
        border_w     = 2 if selected else 1
        pygame.draw.rect(self.surface, border_color, rect, border_w, border_radius=6)

        # Glow effect for selected card (extra outer rect)
        if selected:
            glow = rect.inflate(4, 4)
            glow_surf = pygame.Surface(glow.size, pygame.SRCALPHA)
            r, g, b = char["card_border"]
            pygame.draw.rect(glow_surf, (r, g, b, 50), glow_surf.get_rect(), border_radius=8)
            self.surface.blit(glow_surf, glow.topleft)

        # Portrait
        portrait_rect = pygame.Rect(rect.x, rect.y, rect.w, PORTRAIT_H)
        _draw_portrait(self.surface, portrait_rect, char)

        # Clip portrait to card bounds
        pygame.draw.rect(self.surface, border_color, portrait_rect, 1)

        # Divider
        div_y = rect.y + PORTRAIT_H + 8
        pygame.draw.line(self.surface, (55, 45, 35),
                         (rect.x + 10, div_y), (rect.right - 10, div_y), 1)

        # Name
        name_color = GOLD_TEXT if selected else WHITE
        name_surf  = self._font_name.render(char["name"], True, name_color)
        self.surface.blit(name_surf, name_surf.get_rect(
            centerx=rect.centerx, top=div_y + 6))

        # Title
        title_surf = self._font_subtitle.render(char["title"], True, char["card_border"])
        self.surface.blit(title_surf, title_surf.get_rect(
            centerx=rect.centerx, top=div_y + 46))

        # Tagline
        tag_surf = self._font_stat.render(f'"{char["tagline"]}"', True, (110, 95, 70))
        self.surface.blit(tag_surf, tag_surf.get_rect(
            centerx=rect.centerx, top=div_y + 70))

        # Stat bars
        self._draw_stat_bar(rect.x + 18, div_y + 95,  rect.w - 36,
                            "HP",   char["hp"],       _HP_MAX,      (180,  60,  60))
        self._draw_stat_bar(rect.x + 18, div_y + 117, rect.w - 36,
                            "STAM", char["stamina"],  _STAMINA_MAX, ( 60, 110, 200))
        self._draw_stat_bar(rect.x + 18, div_y + 139, rect.w - 36,
                            "STR",  char["strength"], _STR_MAX,     (200,  95,  50))
        self._draw_stat_bar(rect.x + 18, div_y + 161, rect.w - 36,
                            "AGI",  char["agility"],  _AGI_MAX,     (200, 175,  55))

        # Selected indicator
        if selected:
            ind = self._font_hint.render("▲  SELECTED  ▲", True, char["card_border"])
            self.surface.blit(ind, ind.get_rect(
                centerx=rect.centerx, bottom=rect.bottom - 8))

    def _draw_stat_bar(self, x: int, y: int, w: int,
                       label: str, value: int, max_val: int,
                       color: tuple) -> None:
        label_surf = self._font_stat.render(f"{label}", True, GRAY)
        self.surface.blit(label_surf, (x, y))

        bar_x   = x + 50
        bar_w   = w - 55
        bar_h   = 10
        fill_w  = int(bar_w * min(value / max_val, 1.0))

        pygame.draw.rect(self.surface, (35, 30, 25),   (bar_x, y + 3, bar_w, bar_h),
                         border_radius=3)
        if fill_w > 0:
            pygame.draw.rect(self.surface, color, (bar_x, y + 3, fill_w, bar_h),
                             border_radius=3)

        val_surf = self._font_stat.render(str(value), True, WHITE)
        self.surface.blit(val_surf, (bar_x + bar_w + 6, y))

    # ── Confirmation overlay ──────────────────────────────────────────────────

    def _draw_confirmation(self, char: dict) -> None:
        # Semi-transparent backdrop
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.surface.blit(overlay, (0, 0))

        # Panel
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 320, SCREEN_HEIGHT // 2 - 120, 640, 240)
        pygame.draw.rect(self.surface, (22, 16, 10), panel, border_radius=8)
        pygame.draw.rect(self.surface, char["card_border"], panel, 2, border_radius=8)

        cx = SCREEN_WIDTH // 2

        # Line 1: "Start the challenge as"
        line1 = self._font_confirm2.render("Start the challenge as", True, WHITE)
        self.surface.blit(line1, line1.get_rect(center=(cx, panel.top + 52)))

        # Line 2: character name (gold + large)
        name_surf = self._font_confirm.render(char["name"], True, GOLD_TEXT)
        self.surface.blit(name_surf, name_surf.get_rect(center=(cx, panel.top + 100)))

        # Line 3: title
        title_surf = self._font_confirm2.render(char["title"], True, char["card_border"])
        self.surface.blit(title_surf, title_surf.get_rect(center=(cx, panel.top + 142)))

        # Yes / No
        yes = self._font_confirm2.render("[Y]  Yes", True, (100, 200, 100))
        no  = self._font_confirm2.render("[N]  No",  True, (200, 80,  80))
        self.surface.blit(yes, yes.get_rect(center=(cx - 110, panel.bottom - 42)))
        self.surface.blit(no,  no.get_rect( center=(cx + 110, panel.bottom - 42)))

    # ── Input handlers ────────────────────────────────────────────────────────

    def _handle_selecting(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.selected_idx = (self.selected_idx - 1) % 3
            elif event.key == pygame.K_RIGHT:
                self.selected_idx = (self.selected_idx + 1) % 3
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = "confirming"
            elif event.key == pygame.K_ESCAPE:
                self._result = None
                self._done   = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._card_rects):
                if rect.collidepoint(event.pos):
                    if i == self.selected_idx:
                        self.state = "confirming"
                    else:
                        self.selected_idx = i

    def _handle_confirming(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_y, pygame.K_RETURN):
                self._result = CHARACTERS[self.selected_idx]
                self._done   = True
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                self.state = "selecting"

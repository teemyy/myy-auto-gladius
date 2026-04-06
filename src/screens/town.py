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
_RED    = (200,  60,  60)

# Rarity display colors (grade_level 1–5)
_RARITY_COLORS = {
    1: (170, 170, 170),   # Iron    — gray
    2: (210, 215, 255),   # Steel   — silver-blue
    3: ( 60, 210, 190),   # Mithril — teal
    4: (255, 155,  50),   # Adamantite — orange
    5: (200,  80, 255),   # Draconic — purple
}
_RARITY_NAMES = {1: "Iron", 2: "Steel", 3: "Mithril", 4: "Adamantite", 5: "Draconic"}

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
        self._fd = pygame.font.SysFont(None, 22)

        self._bg: pygame.Surface | None = None
        try:
            raw = pygame.image.load(os.path.join(_ASSETS, "town_bg_1.webp")).convert()
            self._bg = pygame.transform.smoothscale(raw, (_W, _H))
        except (pygame.error, FileNotFoundError):
            pass

        self._btn_rects: dict[str, pygame.Rect] = {
            bid: pygame.Rect(cx - _BTN_W // 2, cy - _BTN_H // 2, _BTN_W, _BTN_H)
            for bid, _, cx, cy in _BUILDINGS
        }
        self._back_rect: pygame.Rect | None = None

        # Store state
        self._store_stock:     list[dict]       = []
        self._store_buy_rects: list[pygame.Rect] = []
        self._store_hover_idx: int              = -1
        self._store_msg:       str              = ""
        self._store_msg_timer: int              = 0

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._store_msg_timer > 0:
            self._store_msg_timer -= 1

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
            if self.state == "store":
                self._store_hover_idx = -1
                for i, rect in enumerate(self._store_buy_rects):
                    if rect.collidepoint(pos):
                        self._store_hover_idx = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "main":
                for bid, rect in self._btn_rects.items():
                    if rect.collidepoint(pos):
                        if bid == "gate":
                            self._done = True
                        else:
                            if bid == "store":
                                self._open_store()
                            self.state = bid
                        return
            elif self.state == "store":
                # Buy button clicks
                for i, rect in enumerate(self._store_buy_rects):
                    if rect.collidepoint(pos) and i < len(self._store_stock):
                        self._try_buy(i)
                        return
                # Refresh button
                if self._refresh_rect and self._refresh_rect.collidepoint(pos):
                    self._open_store()
                    return
                # Back button
                if self._back_rect and self._back_rect.collidepoint(pos):
                    self.state = "main"
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

    # ── Store helpers ────────────────────────────────────────────────────────

    def _open_store(self) -> None:
        if self.equipment:
            self._store_stock = self.equipment.random_store_items(3)
        else:
            self._store_stock = []
        self._store_msg       = ""
        self._store_msg_timer = 0

    def _try_buy(self, idx: int) -> None:
        item = self._store_stock[idx]
        price = item.get("price", 0)
        if self.player.gold < price:
            self._store_msg       = "Not enough gold!"
            self._store_msg_timer = 120
            return
        self.player.gold -= price
        if item["_item_type"] == "weapon":
            self.player.equip_weapon(item)
            self._store_msg = f"Equipped {item['name']}!"
        else:
            self.player.equip_armor(item)
            self._store_msg = f"Equipped {item['name']}!"
        self._store_msg_timer = 120
        # Remove purchased item from stock
        self._store_stock.pop(idx)
        self._store_buy_rects.clear()

    # ── Drawing ──────────────────────────────────────────────────────────────

    def _draw_main(self) -> None:
        if self._bg:
            self.surface.blit(self._bg, (0, 0))
        else:
            self.surface.fill(_DARK)

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

        s = self._fb.render(f"Stage {self.stage}", True, _GOLD)
        self.surface.blit(s, s.get_rect(right=_W - 14, top=12))

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
        dim = pygame.Surface((_W, _H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        self.surface.blit(dim, (0, 0))

        panel = pygame.Rect(_W // 2 - 320, _H // 2 - 240, 640, 480)
        pygame.draw.rect(self.surface, _PANEL, panel, border_radius=8)
        pygame.draw.rect(self.surface, _BORDER, panel, 2, border_radius=8)

        title_txt = _SUB_LABELS.get(self.state, self.state.title())
        title     = self._fa.render(title_txt, True, _GOLD)
        self.surface.blit(title, title.get_rect(centerx=panel.centerx, top=panel.top + 18))
        pygame.draw.line(self.surface, _BORDER,
                         (panel.x + 20, panel.top + 68),
                         (panel.right - 20, panel.top + 68), 1)

        if self.state == "store":
            self._draw_store(panel)
        else:
            cs = self._fb.render("(Coming soon)", True, _GRAY)
            self.surface.blit(cs, cs.get_rect(center=(panel.centerx, panel.centery - 20)))
            self._draw_back_btn(panel)

    def _draw_store(self, panel: pygame.Rect) -> None:
        # Gold display
        gold_s = self._fc.render(f"Your gold:  {self.player.gold} g", True, _GOLD)
        self.surface.blit(gold_s, gold_s.get_rect(right=panel.right - 18, top=panel.top + 74))

        self._store_buy_rects = []
        self._refresh_rect    = None

        if not self._store_stock:
            msg = self._fc.render("No items available.", True, _GRAY)
            self.surface.blit(msg, msg.get_rect(center=(panel.centerx, panel.centery - 20)))
        else:
            row_h  = 100
            row_y0 = panel.top + 82
            for i, item in enumerate(self._store_stock):
                row_y = row_y0 + i * (row_h + 8)
                self._draw_store_row(panel, item, row_y, row_h, i)

        # Status message
        if self._store_msg and self._store_msg_timer > 0:
            col  = _RED if "Not enough" in self._store_msg else _GREEN
            smsg = self._fc.render(self._store_msg, True, col)
            self.surface.blit(smsg, smsg.get_rect(centerx=panel.centerx,
                                                    top=panel.top + 82 + 3 * 108 + 4))

        # Refresh button
        rfr = pygame.Rect(panel.centerx - 200, panel.bottom - 66, 170, 38)
        mouse = pygame.mouse.get_pos()
        rfr_hov = rfr.collidepoint(mouse)
        pygame.draw.rect(self.surface, (25, 20, 14), rfr, border_radius=5)
        pygame.draw.rect(self.surface, _HOVER if rfr_hov else _BORDER, rfr, 2, border_radius=5)
        rl = self._fd.render("↺  Refresh Stock", True, _HOVER if rfr_hov else _GRAY)
        self.surface.blit(rl, rl.get_rect(center=rfr.center))
        self._refresh_rect = rfr

        self._draw_back_btn(panel)

    def _draw_store_row(self, panel: pygame.Rect, item: dict,
                         row_y: int, row_h: int, idx: int) -> None:
        grade_lvl = item.get("grade_level", 1)
        rar_color = _RARITY_COLORS.get(grade_lvl, _GRAY)
        rar_name  = _RARITY_NAMES.get(grade_lvl, "")
        price     = item.get("price", 0)
        itype     = item.get("_item_type", "weapon")
        can_afford = self.player.gold >= price

        row_rect = pygame.Rect(panel.x + 12, row_y, panel.w - 24, row_h)
        pygame.draw.rect(self.surface, (18, 13, 9), row_rect, border_radius=5)
        pygame.draw.rect(self.surface, rar_color, row_rect, 1, border_radius=5)

        tx = row_rect.x + 12
        ty = row_rect.y + 8

        # Item name (rarity-colored)
        name_s = self._fb.render(item["name"], True, rar_color)
        self.surface.blit(name_s, (tx, ty))

        # Rarity badge
        badge_s = self._fd.render(rar_name, True, rar_color)
        self.surface.blit(badge_s, (tx + name_s.get_width() + 10, ty + 5))

        # Type label
        type_label = "Weapon" if itype == "weapon" else "Armor"
        type_s = self._fd.render(type_label, True, _GRAY)
        self.surface.blit(type_s, (tx, ty + 26))

        # Stats summary
        stats_txt = _item_stats_summary(item)
        stats_s   = self._fd.render(stats_txt, True, (160, 150, 120))
        self.surface.blit(stats_s, (tx, ty + 46))

        # Description
        desc = item.get("description", "")[:52]
        desc_s = self._fd.render(desc, True, (100, 90, 70))
        self.surface.blit(desc_s, (tx, ty + 66))

        # Price + Buy button (right side)
        btn_w, btn_h = 110, 34
        btn_x = row_rect.right - btn_w - 10
        btn_y = row_rect.centery - btn_h // 2

        price_col = rar_color if can_afford else _RED
        price_s = self._fb.render(f"{price} g", True, price_col)
        self.surface.blit(price_s, price_s.get_rect(
            right=btn_x - 10, centery=row_rect.centery))

        buy_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        mouse    = pygame.mouse.get_pos()
        hov      = (self._store_hover_idx == idx)

        if can_afford:
            bg_col  = (30, 55, 25)
            bd_col  = (140, 220, 100) if hov else (70, 150, 50)
            txt_col = (180, 255, 140) if hov else (120, 210, 80)
        else:
            bg_col  = (35, 20, 20)
            bd_col  = (100, 55, 55)
            txt_col = (110, 70, 70)

        pygame.draw.rect(self.surface, bg_col,  buy_rect, border_radius=5)
        pygame.draw.rect(self.surface, bd_col,  buy_rect, 2, border_radius=5)
        buy_lbl = self._fc.render("Buy", True, txt_col)
        self.surface.blit(buy_lbl, buy_lbl.get_rect(center=buy_rect.center))

        self._store_buy_rects.append(buy_rect)

    def _draw_back_btn(self, panel: pygame.Rect) -> None:
        back    = pygame.Rect(panel.centerx + 30, panel.bottom - 66, 170, 38)
        mouse   = pygame.mouse.get_pos()
        hovered = back.collidepoint(mouse)
        pygame.draw.rect(self.surface, (35, 26, 16), back, border_radius=6)
        pygame.draw.rect(self.surface, _HOVER if hovered else _BORDER, back, 2, border_radius=6)
        bl = self._fc.render("← Back to Town", True, _HOVER if hovered else _WHITE)
        self.surface.blit(bl, bl.get_rect(center=back.center))
        self._back_rect = back


# ── Helpers ───────────────────────────────────────────────────────────────────

def _item_stats_summary(item: dict) -> str:
    """Return a compact stat string for display in the store row."""
    itype = item.get("_item_type", "weapon")
    if itype == "weapon":
        dmg   = item.get("damage", {})
        parts = [f"{act} {val}" for act, val in dmg.items()]
        dtype = item.get("damage_type") or next(iter(item.get("damage_types", {}).values()), "")
        return f"DMG: {', '.join(parts)}  [{dtype}]"
    else:
        dr    = item.get("damage_reduction", {})
        parts = [f"{k[:3].upper()} ×{v:.2f}" for k, v in dr.items()]
        agi   = item.get("agility_modifier", 0)
        agi_s = f"  AGI {agi:+d}" if agi else ""
        return "  ".join(parts[:3]) + agi_s

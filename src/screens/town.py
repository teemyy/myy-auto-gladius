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
    ("smithy",    "Smithy",          312, 195),
    ("store",     "General Store",   318, 502),
    ("training",  "Training",        898, 472),
    ("gate",      "Enter Arena →",   912, 155),
    ("healer",    "Healer",          640, 658),
    ("inventory", "Inventory",       640, 360),
]
_SUB_LABELS = {
    "smithy":    "Smithy",
    "store":     "General Store",
    "training":  "Training Ground",
    "healer":    "Healer",
    "inventory": "Inventory",
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
        self._store_row_rects: list[pygame.Rect] = []
        self._store_hover_idx: int              = -1  # buy-button hover
        self._store_row_hover: int              = -1  # full-row hover (comparison)
        self._store_msg:       str              = ""
        self._store_msg_timer: int              = 0

        # Inventory state
        self._inv_sell_rects:  list[pygame.Rect] = []
        self._inv_msg:         str              = ""
        self._inv_msg_timer:   int              = 0

        # Healer state (reuses _inv_msg/_inv_msg_timer for status messages)
        self._healer_btn_rects: list[tuple[str, pygame.Rect]] = []

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._store_msg_timer > 0:
            self._store_msg_timer -= 1
        if self._inv_msg_timer > 0:
            self._inv_msg_timer -= 1

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
                self._store_row_hover = -1
                for i, rect in enumerate(self._store_buy_rects):
                    if rect.collidepoint(pos):
                        self._store_hover_idx = i
                for i, rect in enumerate(self._store_row_rects):
                    if rect.collidepoint(pos):
                        self._store_row_hover = i

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
                for i, rect in enumerate(self._store_buy_rects):
                    if rect.collidepoint(pos) and i < len(self._store_stock):
                        self._try_buy(i)
                        return
                if self._refresh_rect and self._refresh_rect.collidepoint(pos):
                    self._open_store()
                    return
                if self._back_rect and self._back_rect.collidepoint(pos):
                    self.state = "main"
            elif self.state == "inventory":
                for i, rect in enumerate(self._inv_sell_rects):
                    if rect.collidepoint(pos):
                        self._try_sell(i)
                        return
                if self._back_rect and self._back_rect.collidepoint(pos):
                    self.state = "main"
            elif self.state == "healer":
                for key, rect in self._healer_btn_rects:
                    if rect.collidepoint(pos):
                        self._healer_service(key)
                        return
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

    def _healer_service(self, key: str) -> None:
        """Handle a healer service purchase. key is 'hp' or a limb name."""
        if key == "hp":
            price = 25
            if self.player.gold < price:
                self._inv_msg = "Not enough gold!"
            elif self.player.hp >= self.player.max_hp:
                self._inv_msg = "HP is already full."
            else:
                self.player.gold -= price
                healed = min(50, self.player.max_hp - self.player.hp)
                self.player.hp += healed
                self._inv_msg = f"Healed {healed} HP."
        else:
            limb = key
            if not self.player.limbs:
                return
            integrity = self.player.limbs.get_integrity(limb)
            price     = 50 if integrity == 0 else 15
            if self.player.gold < price:
                self._inv_msg = "Not enough gold!"
            else:
                self.player.gold -= price
                self.player.limbs.restore_limb(limb, 100)
                self._inv_msg = f"Restored {limb}."
        self._inv_msg_timer = 150

    def _try_sell(self, slot: int) -> None:
        """Sell equipped item: slot 0 = melee weapon, 1 = ranged weapon, 2 = armor."""
        if slot == 0:
            item = self.player.weapon
            if item is None:
                return
            self.player.weapon = None
        elif slot == 1:
            item = self.player.ranged_weapon
            if item is None:
                return
            self.player.ranged_weapon = None
        else:
            item = self.player.armor
            if item is None:
                return
            self.player.equip_armor(None)
        gold = item.get("sell_price", item.get("price", 0) // 2)
        self.player.gold += gold
        self._inv_msg       = f"Sold {item['name']} for {gold} g."
        self._inv_msg_timer = 150

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

            bg_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            bg_surf.fill((14, 10, 6, 210))
            self.surface.blit(bg_surf, rect.topleft)

            bd_col  = _HOVER if hovered else _BORDER
            txt_col = _HOVER if hovered else _GOLD
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
        elif self.state == "inventory":
            self._draw_inventory(panel)
        elif self.state == "healer":
            self._draw_healer(panel)
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

        self._store_row_rects = []
        if not self._store_stock:
            msg = self._fc.render("No items available.", True, _GRAY)
            self.surface.blit(msg, msg.get_rect(center=(panel.centerx, panel.centery - 20)))
        else:
            row_h  = 100
            row_y0 = panel.top + 82
            for i, item in enumerate(self._store_stock):
                row_y = row_y0 + i * (row_h + 8)
                self._draw_store_row(panel, item, row_y, row_h, i)

        # Comparison panel when hovering a weapon
        if (self._store_row_hover >= 0 and self._store_row_hover < len(self._store_stock)):
            hov_item = self._store_stock[self._store_row_hover]
            if hov_item.get("_item_type") == "weapon":
                self._draw_weapon_comparison(hov_item)

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
        self._store_row_rects.append(row_rect)

    def _draw_weapon_comparison(self, store_item: dict) -> None:
        """Draw a comparison panel (right of main panel) for the hovered weapon."""
        cur = self.player.weapon
        if cur is None:
            cur_label = "No weapon"
            cur_dmg   = {}
            cur_crit  = 1.0
            cur_grade = 0
        else:
            cur_label = cur.get("name", "?")
            cur_dmg   = cur.get("damage", {})
            cur_crit  = cur.get("crit_multiplier", 1.0)
            cur_grade = cur.get("grade_level", 1)

        new_dmg  = store_item.get("damage", {})
        new_crit = store_item.get("crit_multiplier", 1.0)
        new_grade = store_item.get("grade_level", 1)

        cw, ch  = 285, 260
        cx_left = _W // 2 + 325   # right of the main panel
        cy_top  = _H // 2 - ch // 2
        cp      = pygame.Rect(cx_left, cy_top, cw, ch)

        pygame.draw.rect(self.surface, (18, 13, 9), cp, border_radius=7)
        pygame.draw.rect(self.surface, _BORDER, cp, 2, border_radius=7)

        tx, ty = cp.x + 12, cp.y + 10
        self.surface.blit(self._fb.render("Comparison", True, _GOLD), (tx, ty))
        ty += 30

        # Current weapon header
        self.surface.blit(self._fd.render("Equipped:", True, _GRAY), (tx, ty))
        self.surface.blit(self._fd.render(cur_label[:22], True, _WHITE), (tx + 80, ty))
        ty += 18

        # New weapon header
        rar = _RARITY_COLORS.get(new_grade, _GRAY)
        self.surface.blit(self._fd.render("Store:", True, _GRAY), (tx, ty))
        self.surface.blit(self._fd.render(store_item["name"][:22], True, rar), (tx + 80, ty))
        ty += 22

        pygame.draw.line(self.surface, _BORDER, (tx, ty), (cp.right - 12, ty), 1)
        ty += 8

        # Stat rows
        all_actions = sorted(set(list(cur_dmg.keys()) + list(new_dmg.keys())))
        for act in all_actions:
            c_val = cur_dmg.get(act, 0)
            n_val = new_dmg.get(act, 0)
            diff  = n_val - c_val
            col   = (100, 220, 100) if diff > 0 else (_RED if diff < 0 else _GRAY)
            diff_s = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "="
            row = f"{act:<8} {c_val:>3}  →  {n_val:>3}  ({diff_s})"
            self.surface.blit(self._fd.render(row, True, col), (tx, ty))
            ty += 18

        # Crit multiplier
        diff_c = new_crit - cur_crit
        col_c  = (100, 220, 100) if diff_c > 0 else (_RED if diff_c < 0 else _GRAY)
        diff_cs = f"+{diff_c:.2f}" if diff_c > 0 else f"{diff_c:.2f}" if diff_c < 0 else "="
        self.surface.blit(
            self._fd.render(f"Crit x  {cur_crit:.2f}  →  {new_crit:.2f}  ({diff_cs})",
                            True, col_c), (tx, ty))
        ty += 18

        # Grade
        diff_g = new_grade - cur_grade
        col_g  = (100, 220, 100) if diff_g > 0 else (_RED if diff_g < 0 else _GRAY)
        diff_gs = f"+{diff_g}" if diff_g > 0 else str(diff_g) if diff_g < 0 else "="
        rar_name = _RARITY_NAMES.get(new_grade, "?")
        self.surface.blit(
            self._fd.render(f"Grade   {_RARITY_NAMES.get(cur_grade,'?'):<12}→  {rar_name}  ({diff_gs})",
                            True, col_g), (tx, ty))

    def _draw_healer(self, panel: pygame.Rect) -> None:
        self._healer_btn_rects = []

        gold_s = self._fc.render(f"Gold:  {self.player.gold} g", True, _GOLD)
        self.surface.blit(gold_s, gold_s.get_rect(right=panel.right - 18, top=panel.top + 74))

        # HP restore row
        hp_full   = self.player.hp >= self.player.max_hp
        hp_price  = 25
        hp_rect   = pygame.Rect(panel.x + 12, panel.top + 82, panel.w - 24, 46)
        self._draw_healer_row(hp_rect, "Restore HP  +50", hp_price,
                              disabled=hp_full or self.player.gold < hp_price,
                              note=f"{self.player.hp}/{self.player.max_hp}")
        self._healer_btn_rects.append(("hp", hp_rect))

        # Limb rows
        if self.player.limbs:
            from ..systems.limb_system import LimbSystem as _LS
            y0 = panel.top + 140
            self.surface.blit(self._fd.render("Limbs:", True, _GRAY), (panel.x + 14, y0))
            y0 += 20
            for limb in _LS.LIMBS:
                integrity = self.player.limbs.get_integrity(limb)
                if integrity == 0:
                    price, svc, col = 50, "Restore (severed)", (255, 80, 80)
                    disabled = self.player.gold < price
                elif integrity <= 50:
                    price, svc, col = 15, "Heal (injured)", (255, 180, 60)
                    disabled = self.player.gold < price
                else:
                    price, svc, col = 0, "Intact", _GREEN
                    disabled = True

                row_rect = pygame.Rect(panel.x + 12, y0, panel.w - 24, 38)
                tx, ty2  = row_rect.x + 10, row_rect.y + 10

                bg_c = (14, 10, 6) if disabled else (22, 16, 10)
                pygame.draw.rect(self.surface, bg_c, row_rect, border_radius=4)
                pygame.draw.rect(self.surface, col if not disabled else (45, 38, 28),
                                 row_rect, 1, border_radius=4)

                self.surface.blit(self._fc.render(f"{limb:<8}  {integrity:>3}", True, col),
                                  (tx, ty2 - 2))
                self.surface.blit(self._fd.render(svc, True, _GRAY if disabled else _WHITE),
                                  (tx + 160, ty2))

                if not disabled and price > 0:
                    btn = pygame.Rect(row_rect.right - 120, row_rect.y + 4, 110, 30)
                    mouse = pygame.mouse.get_pos()
                    hov   = btn.collidepoint(mouse)
                    pygame.draw.rect(self.surface, (28, 22, 14), btn, border_radius=4)
                    pygame.draw.rect(self.surface, _HOVER if hov else _BORDER, btn, 1, border_radius=4)
                    bl = self._fd.render(f"Heal  {price} g", True, _HOVER if hov else _GOLD)
                    self.surface.blit(bl, bl.get_rect(center=btn.center))
                    self._healer_btn_rects.append((limb, btn))

                y0 += 42

        # Status message
        if self._inv_msg and self._inv_msg_timer > 0:
            col_m = _GREEN if "Healed" in self._inv_msg or "Restored" in self._inv_msg else _RED
            ms = self._fc.render(self._inv_msg, True, col_m)
            self.surface.blit(ms, ms.get_rect(centerx=panel.centerx, bottom=panel.bottom - 72))

        self._draw_back_btn(panel)

    def _draw_healer_row(self, rect: pygame.Rect, label: str, price: int,
                          disabled: bool, note: str = "") -> None:
        mouse = pygame.mouse.get_pos()
        hov   = rect.collidepoint(mouse) and not disabled
        pygame.draw.rect(self.surface, (22, 16, 10) if not disabled else (14, 10, 6),
                         rect, border_radius=5)
        pygame.draw.rect(self.surface, (_HOVER if hov else _GOLD) if not disabled else _BORDER,
                         rect, 1, border_radius=5)
        tx, ty = rect.x + 12, rect.y + 8
        col = _HOVER if hov else (_GOLD if not disabled else _GRAY)
        self.surface.blit(self._fc.render(label, True, col), (tx, ty))
        if note:
            self.surface.blit(self._fd.render(note, True, _GRAY),
                              (tx + 200, ty + 4))
        price_col = _GOLD if not disabled else _GRAY
        self.surface.blit(self._fc.render(f"{price} g", True, price_col),
                          (rect.right - 68, ty))

    def _draw_inventory(self, panel: pygame.Rect) -> None:
        self._inv_sell_rects = []

        # Gold display
        gold_s = self._fc.render(f"Gold:  {self.player.gold} g", True, _GOLD)
        self.surface.blit(gold_s, gold_s.get_rect(right=panel.right - 18, top=panel.top + 74))

        slots = [
            ("Melee Weapon",  self.player.weapon),
            ("Ranged Weapon", self.player.ranged_weapon),
            ("Armor",         self.player.armor),
        ]
        row_h  = 110
        row_y0 = panel.top + 82

        for i, (slot_name, item) in enumerate(slots):
            row_y    = row_y0 + i * (row_h + 10)
            row_rect = pygame.Rect(panel.x + 12, row_y, panel.w - 24, row_h)
            pygame.draw.rect(self.surface, (18, 13, 9), row_rect, border_radius=5)

            if item:
                grade_lvl = item.get("grade_level", 1)
                rar_color = _RARITY_COLORS.get(grade_lvl, _GRAY)
                pygame.draw.rect(self.surface, rar_color, row_rect, 1, border_radius=5)
            else:
                pygame.draw.rect(self.surface, (50, 40, 30), row_rect, 1, border_radius=5)

            tx = row_rect.x + 14
            ty = row_rect.y + 10

            # Slot label
            slot_s = self._fd.render(slot_name, True, _GRAY)
            self.surface.blit(slot_s, (tx, ty))

            if item:
                grade_lvl  = item.get("grade_level", 1)
                rar_color  = _RARITY_COLORS.get(grade_lvl, _GRAY)
                rar_name   = _RARITY_NAMES.get(grade_lvl, "")
                sell_price = item.get("sell_price", item.get("price", 0) // 2)

                # Item name
                name_s = self._fb.render(item["name"], True, rar_color)
                self.surface.blit(name_s, (tx, ty + 22))

                # Rarity badge
                badge_s = self._fd.render(rar_name, True, rar_color)
                self.surface.blit(badge_s, (tx + name_s.get_width() + 10, ty + 27))

                # Stats
                stats_txt = _item_stats_summary(item)
                stats_s   = self._fd.render(stats_txt, True, (160, 150, 120))
                self.surface.blit(stats_s, (tx, ty + 56))

                # Description
                desc   = item.get("description", "")[:60]
                desc_s = self._fd.render(desc, True, (100, 90, 70))
                self.surface.blit(desc_s, (tx, ty + 76))

                # Sell button
                btn_w, btn_h = 130, 34
                btn_x = row_rect.right - btn_w - 12
                btn_y = row_rect.y + (row_rect.h - btn_h) // 2
                sell_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                mouse     = pygame.mouse.get_pos()
                hov       = sell_rect.collidepoint(mouse)

                pygame.draw.rect(self.surface, (50, 20, 20), sell_rect, border_radius=5)
                pygame.draw.rect(self.surface, (220, 130, 130) if hov else (160, 70, 70),
                                 sell_rect, 2, border_radius=5)
                sell_lbl = self._fc.render(f"Sell  {sell_price} g", True,
                                           (255, 180, 180) if hov else (200, 100, 100))
                self.surface.blit(sell_lbl, sell_lbl.get_rect(center=sell_rect.center))
                self._inv_sell_rects.append(sell_rect)
            else:
                empty_s = self._fc.render("— nothing equipped —", True, (60, 55, 45))
                self.surface.blit(empty_s, empty_s.get_rect(
                    centerx=row_rect.centerx, centery=row_rect.centery))
                self._inv_sell_rects.append(pygame.Rect(0, 0, 0, 0))  # placeholder

        # Status message
        if self._inv_msg and self._inv_msg_timer > 0:
            col   = _GREEN if "Sold" in self._inv_msg else _RED
            msg_s = self._fc.render(self._inv_msg, True, col)
            self.surface.blit(msg_s, msg_s.get_rect(
                centerx=panel.centerx, top=row_y0 + 2 * (row_h + 10) + 8))

        self._draw_back_btn(panel)

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

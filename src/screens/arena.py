from __future__ import annotations
import os
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..entities.enemy  import Enemy
    from ..systems.combat  import CombatResolver, RoundResult

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images")

# Map player name → idle sprite filename
_IDLE_SPRITES: dict[str, str] = {
    "Yumi": "yumi_idle.jpg",
    "Hana": "hana_idle.jpg",
    "Rei":  "rei_idle.jpg",
}

# ── Layout constants ─────────────────────────────────────────────────────────
_W, _H = 1280, 720

_TOP_BAR_H = 50
_ARENA_H   = 280
_STATUS_H  = 190
_BUTTON_H  = 100
_LOG_H     = _H - _TOP_BAR_H - _ARENA_H - _STATUS_H - _BUTTON_H

_TOP_BAR_Y = 0
_ARENA_Y   = _TOP_BAR_H
_STATUS_Y  = _ARENA_Y + _ARENA_H
_BUTTON_Y  = _STATUS_Y + _STATUS_H
_LOG_Y     = _BUTTON_Y + _BUTTON_H

# Arena tile grid: 8 tiles × 80 px = 640 px, centred
_TILE_W      = 80
_TILE_H      = _ARENA_H
_ARENA_TILES = 8
_ARENA_X     = (_W - _TILE_W * _ARENA_TILES) // 2   # 320

# Combatant sprite size in the arena
_SPRITE_H    = 150
_SPRITE_W    = 150

# Starting tile positions
# Distance 3 at start — within melee range (_RANGE_FAR=4) so combat is immediate
_PLAYER_START_TILE = 2
_ENEMY_START_TILE  = 5

# Distance thresholds
_RANGE_FAR   = 4   # >= : melee auto-misses
_RANGE_CLOSE = 2   # <= : ranged half damage

# Colors
_DARK_BG     = (15, 10, 8)
_PANEL_BG    = (28, 20, 15)
_GOLD        = (220, 175, 60)
_WHITE       = (255, 255, 255)
_GRAY        = (120, 120, 120)
_RED         = (200, 50, 50)
_GREEN       = (50, 180, 80)
_YELLOW      = (210, 180, 40)
_BLUE        = (60, 130, 210)
_DARK_BORDER = (55, 42, 22)

# Button layout — move buttons on the sides, action buttons centred
_BTN_W,  _BTN_H  = 155, 68
_BTN_GAP         = 12
_MOVE_BTN_W      = 120
_MOVE_BTN_H      = 68
_MOVE_BTN_MARGIN = 18   # from screen edge

_ACTIONS_ORDER = ["Heavy", "Quick", "Defend", "Ranged"]


class ArenaScreen:
    """Turn-based battle screen.

    States:
        "player_choose"  -- move (←/→ keys or click) then pick action
        "round_over"     -- showing result; SPACE / click to continue
        "battle_over"    -- win/loss banner; SPACE / click to exit
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
        self.surface  = surface
        self.player   = player
        self.enemy    = enemy
        self.resolver = resolver

        self.state:       str                     = "player_choose"
        self.last_result: "RoundResult | None"    = None
        self.log_lines:   list[str]               = []
        self._done:       bool                    = False
        self._victory:    bool                    = False

        # Ranged-primary players start at maximum distance so their kit shines
        if player.has_ranged_weapon():
            self._player_tile: int = 0
            self._enemy_tile:  int = _ARENA_TILES - 1
        else:
            self._player_tile = _PLAYER_START_TILE
            self._enemy_tile  = _ENEMY_START_TILE
        self._last_player_action: str | None = None

        # Clickable rects populated each draw call
        self._action_btn_rects: dict[str, pygame.Rect] = {}
        self._retreat_btn_rect: pygame.Rect | None     = None
        self._advance_btn_rect: pygame.Rect | None     = None
        self._continue_rect:    pygame.Rect | None     = None

        self._assets_ready = False

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        if not self._assets_ready:
            self._init_assets()

        self.surface.fill(_DARK_BG)
        self._draw_top_bar()
        self._draw_arena_floor()
        self._draw_combatants()
        self._draw_status_panels()
        self._draw_action_menu()
        self._draw_log_bar()

        if self.state == "battle_over":
            self._draw_battle_over_banner()

    def handle_event(self, event: pygame.event.Event) -> None:
        # ── Mouse ─────────────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "player_choose":
                if self._retreat_btn_rect and self._retreat_btn_rect.collidepoint(pos):
                    self._move_player(-1)
                    return
                if self._advance_btn_rect and self._advance_btn_rect.collidepoint(pos):
                    self._move_player(+1)
                    return
                for action, rect in self._action_btn_rects.items():
                    if rect.collidepoint(pos) and action in self.player.available_actions():
                        self._execute_round(action)
                        return
            elif self.state == "round_over":
                if self._continue_rect and self._continue_rect.collidepoint(pos):
                    self._advance_from_round_over()
            elif self.state == "battle_over":
                self._done = True

        # ── Keyboard ──────────────────────────────────────────────────────
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "player_choose":
            if event.key == pygame.K_LEFT:
                self._move_player(-1)
                return
            if event.key == pygame.K_RIGHT:
                self._move_player(+1)
                return
            action = self.ACTION_KEYS.get(event.key)
            if action and action in self.player.available_actions():
                self._execute_round(action)

        elif self.state == "round_over":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance_from_round_over()

        elif self.state == "battle_over":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._done = True

    def is_done(self) -> bool:
        return self._done

    def get_result(self) -> str:
        return "win" if self._victory else "lose"

    def player_won(self) -> bool:
        return self._victory

    # ── State helpers ────────────────────────────────────────────────────────

    def _advance_from_round_over(self) -> None:
        if self.resolver.is_battle_over(self.player, self.enemy):
            self.state = "battle_over"
        else:
            self.state = "player_choose"

    # ── Movement ─────────────────────────────────────────────────────────────

    def _distance(self) -> int:
        return self._enemy_tile - self._player_tile

    def _move_player(self, delta: int) -> None:
        new = self._player_tile + delta
        new = max(0, min(new, _ARENA_TILES - 1))
        if delta > 0 and new >= self._enemy_tile:
            new = self._enemy_tile - 1
        if new != self._player_tile:
            direction = "advances" if delta > 0 else "retreats"
            self._player_tile = new
            self.log_lines.append(
                f"{self.player.name} {direction}. Distance: {self._distance()}"
            )

    def _move_enemy_ai(self) -> None:
        dist = self._distance()
        has_ranged = "Ranged" in self.enemy.weapon.get("available_actions", [])
        if has_ranged:
            if dist < 3:
                self._try_move_enemy(+1)
            elif dist > 5:
                self._try_move_enemy(-1)
        else:
            if dist > 2:
                self._try_move_enemy(-1)

    def _try_move_enemy(self, delta: int) -> None:
        new = self._enemy_tile + delta
        new = max(0, min(new, _ARENA_TILES - 1))
        if delta < 0 and new <= self._player_tile:
            new = self._player_tile + 1
        if new != self._enemy_tile:
            direction = "advances" if delta < 0 else "retreats"
            self._enemy_tile = new
            self.log_lines.append(
                f"{self.enemy.name} {direction}. Distance: {self._distance()}"
            )

    # ── Round handling ────────────────────────────────────────────────────────

    def _execute_round(self, player_action: str) -> None:
        self._move_enemy_ai()

        # Pass the actual last action name (not a log line) to enemy AI
        enemy_action = self.enemy.choose_action(
            player_last_action=self._last_player_action
        )
        self.enemy.record_player_action(player_action)
        self._last_player_action = player_action

        dist   = self._distance()
        result = self.resolver.resolve_round(
            self.player, self.enemy, player_action, enemy_action
        )

        # ── Distance modifiers — applied symmetrically to both sides ─────
        # Far range: player melee misses
        if dist >= _RANGE_FAR and player_action in ("Heavy", "Quick"):
            self.enemy.hp = min(self.enemy.max_hp,
                                self.enemy.hp + result.player_damage_out)
            result.player_damage_out = 0
            result.log.append(
                f"{player_action} misses — {self.enemy.name} is out of reach! (dist {dist})"
            )

        # Far range: enemy melee also misses
        if dist >= _RANGE_FAR and enemy_action in ("Heavy", "Quick"):
            self.player.hp = min(self.player.max_hp,
                                 self.player.hp + result.player_damage_in)
            result.player_damage_in = 0
            result.log.append(
                f"{self.enemy.name}'s {enemy_action} misses — too far! (dist {dist})"
            )

        # Close range: player ranged penalty
        if dist <= _RANGE_CLOSE and player_action == "Ranged" and result.player_damage_out > 0:
            penalty = result.player_damage_out // 2
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + penalty)
            result.player_damage_out -= penalty
            result.log.append(
                f"Ranged penalty — too close! {self.enemy.name} recovers {penalty} HP."
            )

        # Close range: enemy ranged penalty
        if dist <= _RANGE_CLOSE and enemy_action == "Ranged" and result.player_damage_in > 0:
            penalty = result.player_damage_in // 2
            self.player.hp = min(self.player.max_hp, self.player.hp + penalty)
            result.player_damage_in -= penalty
            result.log.append(
                f"{self.enemy.name}'s ranged attack weakened at close range."
            )

        self.last_result = result

        # Always show what both sides did, even if one side's hit was blocked
        self.log_lines.append(
            f"-- {self.player.name}: {player_action}  vs  "
            f"{self.enemy.name}: {enemy_action} --"
        )
        for line in result.log:
            self.log_lines.append(line)

        battle_end = self.resolver.is_battle_over(self.player, self.enemy)
        if battle_end:
            self._victory = (battle_end == "player_win")
            self.state = "battle_over"
        else:
            self.state = "round_over"

    # ── Asset init ────────────────────────────────────────────────────────────

    def _init_assets(self) -> None:
        self._f_title = pygame.font.SysFont(None, 48)
        self._f_sub   = pygame.font.SysFont(None, 32)
        self._f_body  = pygame.font.SysFont(None, 26)
        self._f_small = pygame.font.SysFont(None, 22)
        self._f_hint  = pygame.font.SysFont(None, 22)
        self._f_big   = pygame.font.SysFont(None, 80)

        # Player idle sprite
        fname = _IDLE_SPRITES.get(self.player.name)
        self._player_sprite: pygame.Surface | None = None
        if fname:
            path = os.path.join(_ASSETS, fname)
            try:
                raw = pygame.image.load(path).convert()
                # Remove checkerboard / solid background: sample top-left corner
                corner = raw.get_at((0, 0))[:3]
                raw.set_colorkey(corner, pygame.RLEACCEL)
                self._player_sprite = pygame.transform.smoothscale(
                    raw, (_SPRITE_W, _SPRITE_H)
                )
            except (pygame.error, FileNotFoundError):
                pass

        self._assets_ready = True

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_top_bar(self) -> None:
        pygame.draw.rect(self.surface, (18, 13, 8), (0, _TOP_BAR_Y, _W, _TOP_BAR_H))
        pygame.draw.line(self.surface, _DARK_BORDER, (0, _TOP_BAR_H), (_W, _TOP_BAR_H), 2)

        stage_txt = self._f_sub.render(f"Stage {self.player.stage}", True, _GOLD)
        self.surface.blit(stage_txt, (20, 12))

        grade = self.enemy.weapon.get("grade", "?")
        enemy_txt = self._f_sub.render(
            f"{self.enemy.name}  [{grade} weapon]", True, (200, 80, 80)
        )
        self.surface.blit(enemy_txt,
                          enemy_txt.get_rect(centerx=_W // 2, centery=_TOP_BAR_H // 2))

        hp_pct   = self.enemy.hp / self.enemy.max_hp
        hp_color = _RED if hp_pct < 0.3 else _YELLOW if hp_pct < 0.6 else _GREEN
        hp_txt   = self._f_sub.render(
            f"HP {self.enemy.hp}/{self.enemy.max_hp}", True, hp_color
        )
        self.surface.blit(hp_txt,
                          hp_txt.get_rect(right=_W - 20, centery=_TOP_BAR_H // 2))

    def _draw_arena_floor(self) -> None:
        for i in range(_ARENA_TILES):
            tile_x = _ARENA_X + i * _TILE_W
            color  = (22, 18, 12) if i % 2 == 0 else (26, 20, 14)
            pygame.draw.rect(self.surface, color,
                             (tile_x, _ARENA_Y, _TILE_W, _TILE_H))
        pygame.draw.line(self.surface, _DARK_BORDER,
                         (_ARENA_X, _ARENA_Y + _TILE_H),
                         (_ARENA_X + _TILE_W * _ARENA_TILES, _ARENA_Y + _TILE_H), 2)

        # Distance label
        dist = self._distance()
        if dist >= _RANGE_FAR:
            dc, dl = (200, 100, 50), f"FAR  (dist {dist})"
        elif dist <= _RANGE_CLOSE:
            dc, dl = (50, 180, 120), f"CLOSE  (dist {dist})"
        else:
            dc, dl = _GRAY, f"dist {dist}"
        ds = self._f_small.render(dl, True, dc)
        px_mid = (
            _ARENA_X + self._player_tile * _TILE_W + _TILE_W // 2 +
            _ARENA_X + self._enemy_tile  * _TILE_W + _TILE_W // 2
        ) // 2
        self.surface.blit(ds, ds.get_rect(centerx=px_mid, top=_ARENA_Y + 4))

    def _draw_combatants(self) -> None:
        floor_y = _ARENA_Y + _TILE_H - 8

        # ── Player ───────────────────────────────────────────────────────
        px_center = _ARENA_X + self._player_tile * _TILE_W + _TILE_W // 2
        if self._player_sprite:
            sx = px_center - _SPRITE_W // 2
            sy = floor_y - _SPRITE_H
            self.surface.blit(self._player_sprite, (sx, sy))
        else:
            # Fallback rectangle
            rx = px_center - 28
            ry = floor_y - 100
            pygame.draw.rect(self.surface, (50, 90, 200), (rx, ry, 56, 100), border_radius=4)

        pname = self._f_small.render(self.player.name[:8], True, _WHITE)
        self.surface.blit(pname, pname.get_rect(
            centerx=px_center, bottom=floor_y - _SPRITE_H - 2
        ))

        # ── Enemy — red rectangle ─────────────────────────────────────────
        ex_center = _ARENA_X + self._enemy_tile * _TILE_W + _TILE_W // 2
        erx = ex_center - 28
        ery = floor_y - 100
        pygame.draw.rect(self.surface, (200, 50, 40), (erx, ery, 56, 100), border_radius=4)

        ename = self._f_small.render(self.enemy.name[:10], True, _WHITE)
        self.surface.blit(ename, ename.get_rect(centerx=ex_center, bottom=ery - 2))

        # Last round action labels
        if self.last_result:
            pa = self._f_small.render(f"[{self.last_result.player_action}]", True, _GOLD)
            ea = self._f_small.render(f"[{self.last_result.enemy_action}]", True, (220, 120, 60))
            self.surface.blit(pa, pa.get_rect(
                centerx=px_center, bottom=floor_y - _SPRITE_H - 16
            ))
            self.surface.blit(ea, ea.get_rect(centerx=ex_center, bottom=ery - 16))

    def _draw_status_panels(self) -> None:
        # ── Player panel ─────────────────────────────────────────────────
        p_rect = pygame.Rect(0, _STATUS_Y, _W // 2 - 10, _STATUS_H)
        pygame.draw.rect(self.surface, _PANEL_BG, p_rect)
        pygame.draw.rect(self.surface, _DARK_BORDER, p_rect, 1)
        x0, y0 = p_rect.x + 12, p_rect.y + 10

        self.surface.blit(self._f_sub.render(self.player.name, True, _WHITE), (x0, y0))
        self.surface.blit(
            self._f_body.render(f"Gold: {self.player.gold}", True, _GOLD),
            (x0 + 200, y0 + 4),
        )
        self._draw_bar(x0, y0 + 34, 280, 16,
                       self.player.hp, self.player.max_hp, _RED, "HP")
        self._draw_bar(x0, y0 + 58, 280, 16,
                       self.player.stamina, self.player.max_stamina, _BLUE, "STA")
        self.surface.blit(
            self._f_body.render(f"STR {self.player.strength}", True, (200, 95, 50)),
            (x0, y0 + 84),
        )
        self.surface.blit(
            self._f_body.render(f"AGI {self.player.agility}", True, (200, 175, 55)),
            (x0 + 100, y0 + 84),
        )
        self._draw_limb_grid(x0, y0 + 110, self.player)

        # ── Enemy panel ──────────────────────────────────────────────────
        e_rect = pygame.Rect(_W // 2 + 10, _STATUS_Y, _W // 2 - 10, _STATUS_H)
        pygame.draw.rect(self.surface, _PANEL_BG, e_rect)
        pygame.draw.rect(self.surface, _DARK_BORDER, e_rect, 1)
        ex0, ey0 = e_rect.x + 12, e_rect.y + 10

        self.surface.blit(
            self._f_sub.render(self.enemy.name, True, (200, 80, 80)), (ex0, ey0)
        )
        self._draw_bar(ex0, ey0 + 34, 280, 16,
                       self.enemy.hp, self.enemy.max_hp, _RED, "HP")
        self._draw_bar(ex0, ey0 + 58, 280, 16,
                       self.enemy.stamina, self.enemy.max_stamina, _BLUE, "STA")
        wpn_name  = self.enemy.weapon.get("name", "?")
        wpn_grade = self.enemy.weapon.get("grade", "?")
        arm_type  = self.enemy.armor.get("type", "?") if self.enemy.armor else "None"
        for i, txt in enumerate([
            f"Weapon: {wpn_name} ({wpn_grade})",
            f"Armor:  {arm_type}",
            f"STR {self.enemy.strength}",
        ]):
            color = _GRAY if i < 2 else (200, 95, 50)
            self.surface.blit(self._f_body.render(txt, True, color),
                              (ex0, ey0 + 84 + i * 22))
        self.surface.blit(
            self._f_body.render(f"AGI {self.enemy.agility}", True, (200, 175, 55)),
            (ex0 + 100, ey0 + 84 + 2 * 22),
        )
        self._draw_limb_grid(ex0, ey0 + 152, self.enemy)

    def _draw_bar(self, x, y, w, h, cur, mx, color, label) -> None:
        pct = max(0.0, cur / mx) if mx else 0.0
        pygame.draw.rect(self.surface, (35, 28, 20), (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(self.surface, color, (x, y, int(w * pct), h))
        pygame.draw.rect(self.surface, _DARK_BORDER, (x, y, w, h), 1)
        self.surface.blit(
            self._f_small.render(f"{label} {cur}/{mx}", True, _WHITE),
            (x + 4, y + 1),
        )

    def _draw_limb_grid(self, x, y, entity) -> None:
        from ..systems.limb_system import LimbSystem
        box_w, box_h, gap = 62, 18, 4
        for i, limb in enumerate(LimbSystem.LIMBS):
            integrity = entity.limbs.get_integrity(limb) if entity.limbs else 100
            color = _GREEN if integrity >= 60 else _YELLOW if integrity > 0 else _RED
            bx = x + i * (box_w + gap)
            pygame.draw.rect(self.surface, color, (bx, y, box_w, box_h), border_radius=2)
            lbl = self._f_small.render(f"{limb[:5]} {integrity}", True, _DARK_BG)
            self.surface.blit(lbl, lbl.get_rect(
                center=(bx + box_w // 2, y + box_h // 2)
            ))

    def _draw_action_menu(self) -> None:
        pygame.draw.rect(self.surface, (20, 15, 10), (0, _BUTTON_Y, _W, _BUTTON_H))
        pygame.draw.line(self.surface, _DARK_BORDER, (0, _BUTTON_Y), (_W, _BUTTON_Y), 1)

        # Reset clickable rects
        self._action_btn_rects = {}
        self._retreat_btn_rect = None
        self._advance_btn_rect = None
        self._continue_rect    = None

        cy = _BUTTON_Y + _BUTTON_H // 2

        # ── Continue prompt (round_over) ──────────────────────────────────
        if self.state == "round_over":
            cont_rect = pygame.Rect(_W // 2 - 180, cy - 25, 360, 50)
            pygame.draw.rect(self.surface, (35, 28, 20), cont_rect, border_radius=6)
            pygame.draw.rect(self.surface, _DARK_BORDER, cont_rect, 2, border_radius=6)
            hint = self._f_sub.render("SPACE / click — continue", True, _GRAY)
            self.surface.blit(hint, hint.get_rect(center=cont_rect.center))
            self._continue_rect = cont_rect
            return

        if self.state == "battle_over":
            return

        # ── Movement buttons (sides) ──────────────────────────────────────
        ret_rect = pygame.Rect(
            _MOVE_BTN_MARGIN, cy - _MOVE_BTN_H // 2, _MOVE_BTN_W, _MOVE_BTN_H
        )
        adv_rect = pygame.Rect(
            _W - _MOVE_BTN_MARGIN - _MOVE_BTN_W, cy - _MOVE_BTN_H // 2,
            _MOVE_BTN_W, _MOVE_BTN_H,
        )
        for rect, label, arrow in (
            (ret_rect, "Retreat", "◀"),
            (adv_rect, "Advance", "▶"),
        ):
            pygame.draw.rect(self.surface, (30, 22, 14), rect, border_radius=6)
            pygame.draw.rect(self.surface, (80, 65, 40), rect, 2, border_radius=6)
            s1 = self._f_small.render(arrow, True, _GOLD)
            s2 = self._f_small.render(label, True, _GRAY)
            self.surface.blit(s1, s1.get_rect(center=(rect.centerx, rect.centery - 10)))
            self.surface.blit(s2, s2.get_rect(center=(rect.centerx, rect.centery + 10)))
        self._retreat_btn_rect = ret_rect
        self._advance_btn_rect = adv_rect

        # ── Action buttons (centred between the move buttons) ─────────────
        available = self.player.available_actions()

        # Only show buttons for actions the player's weapon supports + Defend.
        # This prevents showing permanently-grayed Quick for axe/bow users.
        weapon_actions = (
            self.player.weapon.get("available_actions", ["Heavy", "Quick"])
            if self.player.weapon else ["Heavy", "Quick"]
        )
        actions = [a for a in _ACTIONS_ORDER
                   if a in weapon_actions or a == "Defend"]

        zone_x1 = ret_rect.right + 10
        zone_x2 = adv_rect.left  - 10
        zone_w   = zone_x2 - zone_x1
        total_w  = len(actions) * _BTN_W + (len(actions) - 1) * _BTN_GAP
        start_x  = zone_x1 + (zone_w - total_w) // 2

        for i, action in enumerate(actions):
            bx      = start_x + i * (_BTN_W + _BTN_GAP)
            by      = cy - _BTN_H // 2
            enabled = action in available
            dist    = self._distance()

            if action in ("Heavy", "Quick") and dist >= _RANGE_FAR:
                bg, border, text_c = (25, 18, 12), (100, 60, 40), (100, 80, 60)
                warn = True
            elif action == "Ranged" and dist <= _RANGE_CLOSE:
                bg, border, text_c = (35, 26, 16), (160, 140, 60), (200, 180, 80)
                warn = False
            else:
                bg     = (35, 26, 16) if enabled else (22, 18, 14)
                border = _GOLD if enabled else (55, 45, 35)
                text_c = _WHITE if enabled else (70, 65, 60)
                warn   = False

            btn_rect = pygame.Rect(bx, by, _BTN_W, _BTN_H)
            pygame.draw.rect(self.surface, bg,     btn_rect, border_radius=6)
            pygame.draw.rect(self.surface, border, btn_rect, 2, border_radius=6)

            self.surface.blit(
                self._f_small.render(f"[{i + 1}]", True, _GOLD if enabled else _GRAY),
                (bx + 8, by + 8),
            )
            self.surface.blit(
                self._f_sub.render(action, True, text_c),
                self._f_sub.render(action, True, text_c).get_rect(
                    center=(bx + _BTN_W // 2, by + _BTN_H // 2 + 4)
                ),
            )
            if warn:
                ms = self._f_small.render("OUT OF RANGE", True, (180, 80, 40))
                self.surface.blit(ms, ms.get_rect(
                    centerx=bx + _BTN_W // 2, bottom=by + _BTN_H - 4
                ))

            self._action_btn_rects[action] = btn_rect

    def _draw_log_bar(self) -> None:
        log_rect = pygame.Rect(0, _LOG_Y, _W, _LOG_H)
        pygame.draw.rect(self.surface, (12, 9, 6), log_rect)
        pygame.draw.line(self.surface, _DARK_BORDER, (0, _LOG_Y), (_W, _LOG_Y), 1)

        max_lines = max(1, _LOG_H // 18)
        for i, line in enumerate(self.log_lines[-max_lines:]):
            if "CRITICAL" in line:
                color = (240, 160, 60)
            elif "destroyed" in line or "evades" in line:
                color = (220, 90, 70)
            elif "misses" in line or "penalty" in line:
                color = (180, 130, 60)
            elif "advances" in line or "retreats" in line:
                color = (80, 140, 180)
            else:
                color = (160, 145, 110)
            self.surface.blit(
                self._f_hint.render(line, True, color),
                (8, _LOG_Y + 4 + i * 18),
            )

    def _draw_battle_over_banner(self) -> None:
        overlay = pygame.Surface((_W, _H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.surface.blit(overlay, (0, 0))

        title_txt = "VICTORY" if self._victory else "DEFEATED"
        title_clr = (80, 220, 80) if self._victory else (220, 60, 60)
        sub_txt   = (f"+{self.enemy.gold_reward} gold"
                     if self._victory else "You have fallen in the arena.")

        cx, cy = _W // 2, _H // 2
        self.surface.blit(
            self._f_big.render(title_txt, True, title_clr),
            self._f_big.render(title_txt, True, title_clr).get_rect(center=(cx, cy - 60)),
        )
        self.surface.blit(
            self._f_sub.render(sub_txt, True, _GRAY),
            self._f_sub.render(sub_txt, True, _GRAY).get_rect(center=(cx, cy + 10)),
        )
        self.surface.blit(
            self._f_hint.render("SPACE / click to continue", True, (100, 90, 70)),
            self._f_hint.render("SPACE / click to continue", True, (100, 90, 70))
            .get_rect(center=(cx, cy + 60)),
        )

    # ── Unused stubs kept for API compatibility ───────────────────────────────

    def _draw_combatant_panel(self, entity, rect: pygame.Rect, flip: bool = False) -> None:
        pass

    def _draw_round_log(self) -> None:
        pass

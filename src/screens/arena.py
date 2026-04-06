from __future__ import annotations
import os
import pygame
from typing import TYPE_CHECKING
from ._anim import (
    AnimSys, AState,
    quick_atk, heavy_atk, defend_anim,
    hit_flash, sprite_knockback, screen_shake,
    miss_flash, death_anim, screen_fade, hold_black,
)

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..entities.enemy  import Enemy
    from ..systems.combat  import CombatResolver, RoundResult

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images")

_IDLE_SPRITES: dict[str, str] = {
    "Yumi": "yumi_idle.jpg",
    "Hana": "hana_idle.jpg",
    "Rei":  "rei_idle.jpg",
}
_ENEMY_SPRITES: dict[str, str] = {
    "slave_gladiator": "slave_gladiator_idle.jpg",
}

# ── Layout ────────────────────────────────────────────────────────────────────
_W, _H       = 1280, 720
_TOP_BAR_H   = 50
_ARENA_H     = 280
_STATUS_H    = 190
_BUTTON_H    = 100
_LOG_H       = _H - _TOP_BAR_H - _ARENA_H - _STATUS_H - _BUTTON_H
_TOP_BAR_Y   = 0
_ARENA_Y     = _TOP_BAR_H
_STATUS_Y    = _ARENA_Y + _ARENA_H
_BUTTON_Y    = _STATUS_Y + _STATUS_H
_LOG_Y       = _BUTTON_Y + _BUTTON_H

_TILE_W      = 80
_TILE_H      = _ARENA_H
_ARENA_TILES = 8
_ARENA_X     = (_W - _TILE_W * _ARENA_TILES) // 2
_SPRITE_H    = 150
_SPRITE_W    = 150

_PLAYER_START_TILE = 2
_ENEMY_START_TILE  = 5
_RANGE_FAR         = 4
_RANGE_CLOSE       = 2

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
_LIMB_DEAD   = (100, 15, 15)

# Button layout
_BTN_W, _BTN_H   = 155, 68
_BTN_GAP         = 12
_MOVE_BTN_W      = 120
_MOVE_BTN_H      = 68
_MOVE_BTN_MARGIN = 18
_ACTIONS_ORDER   = ["Heavy", "Quick", "Defend", "Ranged"]


def _enemy_id_from_name(name: str) -> str:
    return name.lower().replace(" ", "_")


# ═══════════════════════════════════════════════════════════════════════════════
class ArenaScreen:
    """Turn-based battle screen.

    States: "player_choose" | "round_over" | "battle_over"
    Input is locked while self._anim.busy() is True.
    """

    ACTION_KEYS = {
        pygame.K_1: "Heavy",
        pygame.K_2: "Quick",
        pygame.K_3: "Defend",
        pygame.K_4: "Ranged",
    }

    def __init__(self, surface: pygame.Surface, player: "Player",
                 enemy: "Enemy", resolver: "CombatResolver") -> None:
        self.surface  = surface
        self.player   = player
        self.enemy    = enemy
        self.resolver = resolver

        self.state:       str                  = "player_choose"
        self.last_result: "RoundResult | None" = None
        self.log_lines:   list[str]            = []
        self._done:       bool                 = False
        self._victory:    bool                 = False

        if player.has_ranged_weapon():
            self._player_tile: int = 0
            self._enemy_tile:  int = _ARENA_TILES - 1
        else:
            self._player_tile = _PLAYER_START_TILE
            self._enemy_tile  = _ENEMY_START_TILE
        self._last_player_action: str | None = None

        # Animation system
        self._anim = AnimSys()
        self._player_limb_flash: dict[str, int] = {}
        self._enemy_limb_flash:  dict[str, int] = {}

        # Clickable rects (populated each draw)
        self._action_btn_rects: dict[str, pygame.Rect] = {}
        self._retreat_btn_rect: pygame.Rect | None     = None
        self._advance_btn_rect: pygame.Rect | None     = None
        self._continue_rect:    pygame.Rect | None     = None

        self._assets_ready = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._anim.tick()
        for d in (self._player_limb_flash, self._enemy_limb_flash):
            for k in list(d):
                d[k] -= 1
                if d[k] <= 0:
                    del d[k]

    def draw(self) -> None:
        if not self._assets_ready:
            self._init_assets()

        rs = self._render_surf
        rs.fill(_DARK_BG)
        self._draw_top_bar(rs)
        self._draw_arena_floor(rs)
        self._draw_combatants(rs)
        self._draw_status_panels(rs)
        self._draw_action_menu(rs)
        self._draw_log_bar(rs)
        if self.state == "battle_over":
            self._draw_battle_over_banner(rs)
        self._draw_float_texts(rs)

        # Blit render surface with shake offset
        st = self._anim.state
        self.surface.fill(_DARK_BG)
        self.surface.blit(rs, (st.screen_dx, st.screen_dy))

        # Full-screen fade-to-black overlay
        if st.overlay_alpha > 0:
            ov = pygame.Surface((_W, _H))
            ov.fill((0, 0, 0))
            ov.set_alpha(st.overlay_alpha)
            self.surface.blit(ov, (0, 0))

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._anim.busy():
            return  # lock input during animation

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "player_choose":
                if self._retreat_btn_rect and self._retreat_btn_rect.collidepoint(pos):
                    self._move_player(-1); return
                if self._advance_btn_rect and self._advance_btn_rect.collidepoint(pos):
                    self._move_player(+1); return
                for action, rect in self._action_btn_rects.items():
                    if rect.collidepoint(pos) and action in self.player.available_actions():
                        self._execute_round(action); return
            elif self.state == "round_over":
                if self._continue_rect and self._continue_rect.collidepoint(pos):
                    self._advance_from_round_over()
            elif self.state == "battle_over":
                self._done = True

        if event.type != pygame.KEYDOWN:
            return

        if self.state == "player_choose":
            if event.key == pygame.K_LEFT:  self._move_player(-1); return
            if event.key == pygame.K_RIGHT: self._move_player(+1); return
            action = self.ACTION_KEYS.get(event.key)
            if action and action in self.player.available_actions():
                self._execute_round(action)
        elif self.state == "round_over":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._advance_from_round_over()
        elif self.state == "battle_over":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._done = True

    def is_done(self)    -> bool: return self._done
    def get_result(self) -> str:  return "win" if self._victory else "lose"
    def player_won(self) -> bool: return self._victory

    # ── State helpers ─────────────────────────────────────────────────────────

    def _advance_from_round_over(self) -> None:
        if self.resolver.is_battle_over(self.player, self.enemy):
            self.state = "battle_over"
        else:
            self.state = "player_choose"

    # ── Movement ──────────────────────────────────────────────────────────────

    def _distance(self) -> int:
        return self._enemy_tile - self._player_tile

    def _move_player(self, delta: int) -> None:
        new = max(0, min(self._player_tile + delta, _ARENA_TILES - 1))
        if delta > 0 and new >= self._enemy_tile:
            new = self._enemy_tile - 1
        if new != self._player_tile:
            self._player_tile = new
            self.log_lines.append(
                f"{self.player.name} {'advances' if delta > 0 else 'retreats'}."
                f" Distance: {self._distance()}"
            )
        self._enemy_action_on_move()

    def _enemy_action_on_move(self) -> None:
        """Enemy takes a free action while the player repositions."""
        enemy_action = self.enemy.choose_action(player_last_action=self._last_player_action)
        self.resolver.consume_stamina(self.enemy, enemy_action)

        dist       = self._distance()
        dmg_in     = 0
        is_crit    = False
        pending    = [f"  {self.enemy.name}: {enemy_action}"]

        if enemy_action in ("Heavy", "Quick", "Ranged"):
            in_range = (dist < _RANGE_FAR) if enemy_action != "Ranged" else True
            if in_range:
                weapon   = self.enemy.weapon or {}
                base_dmg = weapon.get("damage", {}).get(enemy_action, 5)
                dmg_type = (weapon.get("damage_types", {}).get(enemy_action)
                            or weapon.get("damage_type", "slashing"))
                arm_type = self.player.armor.get("type", "Cloth") if self.player.armor else "Cloth"
                is_crit  = self.resolver.roll_critical(self.enemy.agility)
                if self.resolver.roll_evasion(self.player.agility):
                    pending.append(f"  {self.player.name} evades!")
                else:
                    dmg = self.resolver.calculate_damage(
                        base_dmg, dmg_type, arm_type,
                        self.enemy.strength, self.player.strength, is_crit,
                    )
                    if enemy_action == "Ranged" and dist <= _RANGE_CLOSE:
                        dmg = max(1, dmg // 2)
                    dmg_in = self.player.take_damage(dmg)
                    tag    = "CRITICAL! " if is_crit else ""
                    pending.append(f"  {tag}{self.enemy.name} hits {self.player.name} "
                                   f"with {enemy_action} for {dmg_in}!")
                    # Heavy knockback during move
                    if enemy_action == "Heavy":
                        new_pt = max(0, self._player_tile - 1)
                        if new_pt != self._player_tile:
                            self._player_tile = new_pt
                            pending.append(f"  {self.player.name} is knocked back! "
                                           f"(dist {self._distance()})")
            else:
                pending.append(f"  {self.enemy.name}'s {enemy_action} misses — out of range.")
        else:
            pending.append(f"  {self.enemy.name} takes a defensive stance.")

        # Queue animations
        _atk = {"Quick": quick_atk, "Heavy": heavy_atk, "Defend": defend_anim}
        if enemy_action in _atk:
            self._anim.add(_atk[enemy_action](False))

        floor_top = float(_ARENA_Y + _TILE_H - _SPRITE_H - 12)
        if dmg_in > 0:
            self._anim.add(hit_flash(True, is_crit))
            self._anim.add(sprite_knockback(True, -30.0 if enemy_action == "Heavy" else -15.0))
            if enemy_action == "Heavy":
                self._anim.add(screen_shake(10 if is_crit else 5, 6))
            self._anim.float_text(
                str(dmg_in),
                (255, 220, 50) if is_crit else (255, 160, 100),
                self._player_screen_cx(), floor_top,
                36 if is_crit else 28,
            )

        def _on_done() -> None:
            self.log_lines.extend(pending)
            if not self.player.is_alive:
                self._victory = False
                self._anim.add(death_anim(True), screen_fade())
                def _after_death() -> None:
                    self._anim.add(hold_black(120))
                    self._anim.on_done(lambda: setattr(self, "state", "battle_over"))
                self._anim.on_done(_after_death)

        self._anim.on_done(_on_done)

    def _move_enemy_ai(self) -> None:
        dist       = self._distance()
        has_ranged = "Ranged" in self.enemy.weapon.get("available_actions", [])
        if has_ranged:
            if dist < 3: self._try_move_enemy(+1)
            elif dist > 5: self._try_move_enemy(-1)
        elif dist > 2:
            self._try_move_enemy(-1)

    def _try_move_enemy(self, delta: int) -> None:
        new = max(0, min(self._enemy_tile + delta, _ARENA_TILES - 1))
        if delta < 0 and new <= self._player_tile:
            new = self._player_tile + 1
        if new != self._enemy_tile:
            self._enemy_tile = new
            self.log_lines.append(
                f"{self.enemy.name} {'advances' if delta < 0 else 'retreats'}."
                f" Distance: {self._distance()}"
            )

    # ── Position helpers ──────────────────────────────────────────────────────

    def _player_screen_cx(self) -> float:
        return _ARENA_X + self._player_tile * _TILE_W + _TILE_W / 2.0

    def _enemy_screen_cx(self) -> float:
        return _ARENA_X + self._enemy_tile * _TILE_W + _TILE_W / 2.0

    # ── Animation queuing ─────────────────────────────────────────────────────

    def _queue_combat_anims(self, player_action: str, enemy_action: str,
                             result: "RoundResult") -> None:
        floor_top = float(_ARENA_Y + _TILE_H - _SPRITE_H - 12)

        # Attack animations
        _atk = {
            "Quick":  quick_atk,
            "Heavy":  heavy_atk,
            "Defend": defend_anim,
        }
        if player_action in _atk: self._anim.add(_atk[player_action](True))
        if enemy_action  in _atk: self._anim.add(_atk[enemy_action](False))

        # Enemy receives damage
        if result.player_damage_out > 0:
            crit = result.player_crit
            self._anim.add(hit_flash(False, crit))
            self._anim.add(sprite_knockback(False, +30.0 if player_action == "Heavy" else +15.0))
            if player_action == "Heavy":
                self._anim.add(screen_shake(10 if crit else 5, 6))
            self._anim.float_text(
                str(result.player_damage_out),
                (255, 220, 50) if crit else _WHITE,
                self._enemy_screen_cx(), floor_top,
                36 if crit else 28,
            )
        elif result.outcome in ("attacker_hits", "both_hit"):
            self._anim.add(miss_flash(False))
            self._anim.float_text("MISS", _WHITE, self._enemy_screen_cx(), floor_top)

        # Player receives damage
        if result.player_damage_in > 0:
            crit = result.enemy_crit
            self._anim.add(hit_flash(True, crit))
            self._anim.add(sprite_knockback(True, -30.0 if enemy_action == "Heavy" else -15.0))
            if enemy_action == "Heavy":
                self._anim.add(screen_shake(10 if crit else 5, 6))
            self._anim.float_text(
                str(result.player_damage_in),
                (255, 220, 50) if crit else (255, 160, 100),
                self._player_screen_cx(), floor_top,
                36 if crit else 28,
            )
        elif result.outcome in ("defender_hits", "both_hit"):
            self._anim.add(miss_flash(True))
            self._anim.float_text("MISS", _WHITE, self._player_screen_cx(), floor_top)

        # Limb injury floats
        for limb in result.new_enemy_wounds:
            self._enemy_limb_flash[limb] = 20
            self._anim.float_text(f"{limb} INJURED!", (255, 130, 0),
                                   self._enemy_screen_cx(), floor_top - 22, 22)
        for limb in result.new_player_wounds:
            self._player_limb_flash[limb] = 20
            self._anim.float_text(f"{limb} INJURED!", (255, 130, 0),
                                   self._player_screen_cx(), floor_top - 22, 22)

    # ── Round handling ────────────────────────────────────────────────────────

    def _execute_round(self, player_action: str) -> None:
        self._move_enemy_ai()

        enemy_action = self.enemy.choose_action(player_last_action=self._last_player_action)
        self.enemy.record_player_action(player_action)
        self._last_player_action = player_action

        dist   = self._distance()
        result = self.resolver.resolve_round(self.player, self.enemy, player_action, enemy_action)

        # Distance modifiers
        if dist >= _RANGE_FAR and player_action in ("Heavy", "Quick"):
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + result.player_damage_out)
            result.player_damage_out = 0
            result.log.append(f"{player_action} misses — {self.enemy.name} is out of reach! (dist {dist})")

        if dist >= _RANGE_FAR and enemy_action in ("Heavy", "Quick"):
            self.player.hp = min(self.player.max_hp, self.player.hp + result.player_damage_in)
            result.player_damage_in = 0
            result.log.append(f"{self.enemy.name}'s {enemy_action} misses — too far! (dist {dist})")

        if dist <= _RANGE_CLOSE and player_action == "Ranged" and result.player_damage_out > 0:
            penalty = result.player_damage_out // 2
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + penalty)
            result.player_damage_out -= penalty
            result.log.append(f"Ranged penalty — too close! {self.enemy.name} recovers {penalty} HP.")

        if dist <= _RANGE_CLOSE and enemy_action == "Ranged" and result.player_damage_in > 0:
            penalty = result.player_damage_in // 2
            self.player.hp = min(self.player.max_hp, self.player.hp + penalty)
            result.player_damage_in -= penalty
            result.log.append(f"{self.enemy.name}'s ranged attack weakened at close range.")

        # Heavy knockback
        if player_action == "Heavy" and result.player_damage_out > 0:
            new_et = min(_ARENA_TILES - 1, self._enemy_tile + 1)
            if new_et != self._enemy_tile:
                self._enemy_tile = new_et
                result.log.append(f"{self.enemy.name} is knocked back! (dist {self._distance()})")

        if enemy_action == "Heavy" and result.player_damage_in > 0:
            new_pt = max(0, self._player_tile - 1)
            if new_pt != self._player_tile:
                self._player_tile = new_pt
                result.log.append(f"{self.player.name} is knocked back! (dist {self._distance()})")

        self.last_result = result

        # Collect log — shown after animations complete
        pending_log = [
            f"-- {self.player.name}: {player_action}  vs  {self.enemy.name}: {enemy_action} --"
        ]
        pending_log.extend(result.log)

        # Queue animations (parallel tracks)
        self._queue_combat_anims(player_action, enemy_action, result)

        def _on_done() -> None:
            self.log_lines.extend(pending_log)
            battle_end = self.resolver.is_battle_over(self.player, self.enemy)
            if battle_end:
                self._victory = (battle_end == "player_win")
                dying_player  = (battle_end == "enemy_win")
                # death + fade in parallel, then hold black 2 s, then show banner
                self._anim.add(death_anim(dying_player), screen_fade())
                def _after_death() -> None:
                    self._anim.add(hold_black(120))   # 2 s at 60 fps
                    self._anim.on_done(lambda: setattr(self, "state", "battle_over"))
                self._anim.on_done(_after_death)
            else:
                self.state = "round_over"

        self._anim.on_done(_on_done)

    # ── Asset init ────────────────────────────────────────────────────────────

    def _init_assets(self) -> None:
        self._f_title = pygame.font.SysFont(None, 48)
        self._f_sub   = pygame.font.SysFont(None, 32)
        self._f_body  = pygame.font.SysFont(None, 26)
        self._f_small = pygame.font.SysFont(None, 22)
        self._f_hint  = pygame.font.SysFont(None, 22)
        self._f_big   = pygame.font.SysFont(None, 80)

        self._render_surf = pygame.Surface((_W, _H))
        self._bold_cache: dict[int, pygame.font.Font] = {}

        self._player_sprite: pygame.Surface | None = None
        self._enemy_sprite:  pygame.Surface | None = None
        self._enemy_sprite_flipped: pygame.Surface | None = None

        for attr, fname in (
            ("_player_sprite", _IDLE_SPRITES.get(self.player.name)),
            ("_enemy_sprite",  _ENEMY_SPRITES.get(
                getattr(self.enemy, "id", None) or _enemy_id_from_name(self.enemy.name)
            )),
        ):
            if fname:
                path = os.path.join(_ASSETS, fname)
                try:
                    raw    = pygame.image.load(path).convert()
                    corner = raw.get_at((0, 0))[:3]
                    raw.set_colorkey(corner, pygame.RLEACCEL)
                    setattr(self, attr, pygame.transform.smoothscale(raw, (_SPRITE_W, _SPRITE_H)))
                except (pygame.error, FileNotFoundError):
                    pass

        if self._enemy_sprite:
            self._enemy_sprite_flipped = pygame.transform.flip(self._enemy_sprite, True, False)

        self._bg_image: pygame.Surface | None = None
        try:
            raw = pygame.image.load(os.path.join(_ASSETS, "arena_bg_1.jpg")).convert()
            self._bg_image = pygame.transform.smoothscale(raw, (_W, _ARENA_H))
        except (pygame.error, FileNotFoundError):
            pass

        self._assets_ready = True

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _bold_font(self, size: int) -> pygame.font.Font:
        if size not in self._bold_cache:
            self._bold_cache[size] = pygame.font.SysFont(None, size, bold=True)
        return self._bold_cache[size]

    def _draw_top_bar(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (18, 13, 8), (0, _TOP_BAR_Y, _W, _TOP_BAR_H))
        pygame.draw.line(surface, _DARK_BORDER, (0, _TOP_BAR_H), (_W, _TOP_BAR_H), 2)

        stage_txt = self._f_sub.render(f"Stage {self.player.stage}", True, _GOLD)
        surface.blit(stage_txt, (20, 12))

        grade     = self.enemy.weapon.get("grade", "?")
        enemy_txt = self._f_sub.render(f"{self.enemy.name}  [{grade} weapon]", True, (200, 80, 80))
        surface.blit(enemy_txt, enemy_txt.get_rect(centerx=_W // 2, centery=_TOP_BAR_H // 2))

        hp_pct   = self.enemy.hp / self.enemy.max_hp
        hp_color = _RED if hp_pct < 0.3 else _YELLOW if hp_pct < 0.6 else _GREEN
        hp_txt   = self._f_sub.render(f"HP {self.enemy.hp}/{self.enemy.max_hp}", True, hp_color)
        surface.blit(hp_txt, hp_txt.get_rect(right=_W - 20, centery=_TOP_BAR_H // 2))

    def _draw_arena_floor(self, surface: pygame.Surface) -> None:
        if self._bg_image:
            surface.blit(self._bg_image, (0, _ARENA_Y))
        else:
            for i in range(_ARENA_TILES):
                color = (22, 18, 12) if i % 2 == 0 else (26, 20, 14)
                pygame.draw.rect(surface, color,
                                 (_ARENA_X + i * _TILE_W, _ARENA_Y, _TILE_W, _TILE_H))
        pygame.draw.line(surface, _DARK_BORDER, (0, _ARENA_Y + _TILE_H), (_W, _ARENA_Y + _TILE_H), 2)

        dist = self._distance()
        dc   = (200, 100, 50) if dist >= _RANGE_FAR else (50, 180, 120) if dist <= _RANGE_CLOSE else _GRAY
        dl   = ("FAR" if dist >= _RANGE_FAR else "CLOSE" if dist <= _RANGE_CLOSE else f"dist {dist}") + f"  ({dist})"
        ds   = self._f_small.render(dl, True, dc)
        mid  = int((self._player_screen_cx() + self._enemy_screen_cx()) / 2)
        surface.blit(ds, ds.get_rect(centerx=mid, top=_ARENA_Y + 4))

    def _apply_sprite(self, surface: pygame.Surface, spr: pygame.Surface,
                      cx: int, floor_y: int, angle: float, alpha: int,
                      tint: tuple | None) -> int:
        """Transform + blit one sprite. Returns the sprite's top y (for label anchoring)."""
        if angle:
            spr = pygame.transform.rotate(spr, angle)
        sx = cx - spr.get_width()  // 2
        sy = floor_y - spr.get_height()
        if alpha != 255:
            spr = spr.copy()
            spr.set_alpha(alpha)
        surface.blit(spr, (sx, sy))
        if tint:
            r, g, b, a = tint
            t = pygame.Surface(spr.get_size(), pygame.SRCALPHA)
            t.fill((r, g, b, a))
            surface.blit(t, (sx, sy))
        return sy

    def _draw_combatants(self, surface: pygame.Surface) -> None:
        st      = self._anim.state
        floor_y = _ARENA_Y + _TILE_H - 8

        # ── Player ────────────────────────────────────────────────────────
        px_base   = _ARENA_X + self._player_tile * _TILE_W + _TILE_W // 2
        px_center = px_base + int(st.player_atk_x + st.player_kb_x)

        if self._player_sprite:
            spr_top = self._apply_sprite(surface, self._player_sprite,
                                         px_center, floor_y,
                                         st.player_angle, st.player_alpha, st.player_tint)
        else:
            rx = px_center - 28
            ry = floor_y - 100
            pygame.draw.rect(surface, (50, 90, 200), (rx, ry, 56, 100), border_radius=4)
            spr_top = ry

        pname = self._f_small.render(self.player.name[:8], True, _WHITE)
        surface.blit(pname, pname.get_rect(centerx=px_base, bottom=spr_top - 2))

        # ── Enemy ─────────────────────────────────────────────────────────
        ex_base   = _ARENA_X + self._enemy_tile * _TILE_W + _TILE_W // 2
        ex_center = ex_base + int(st.enemy_atk_x + st.enemy_kb_x)

        if self._enemy_sprite_flipped:
            spr = self._enemy_sprite_flipped
            if st.enemy_angle:
                spr = pygame.transform.rotate(spr, -st.enemy_angle)
            esx     = ex_center - spr.get_width() // 2
            esy     = floor_y   - spr.get_height()
            if st.enemy_alpha != 255:
                spr = spr.copy()
                spr.set_alpha(st.enemy_alpha)
            surface.blit(spr, (esx, esy))
            if st.enemy_tint:
                r, g, b, a = st.enemy_tint
                t = pygame.Surface(spr.get_size(), pygame.SRCALPHA)
                t.fill((r, g, b, a))
                surface.blit(t, (esx, esy))
            ename_top = esy
        else:
            erx = ex_center - 28
            ery = floor_y - 100
            pygame.draw.rect(surface, (200, 50, 40), (erx, ery, 56, 100), border_radius=4)
            ename_top = ery

        ename = self._f_small.render(self.enemy.name[:10], True, _WHITE)
        surface.blit(ename, ename.get_rect(centerx=ex_base, bottom=ename_top - 2))

        if self.last_result:
            pa = self._f_small.render(f"[{self.last_result.player_action}]", True, _GOLD)
            ea = self._f_small.render(f"[{self.last_result.enemy_action}]", True, (220, 120, 60))
            surface.blit(pa, pa.get_rect(centerx=px_base, bottom=spr_top    - 16))
            surface.blit(ea, ea.get_rect(centerx=ex_base, bottom=ename_top  - 16))

    def _draw_float_texts(self, surface: pygame.Surface) -> None:
        for ft in self._anim._ft:
            progress = ft.age / ft.max_age
            cur_y    = ft.y - 40.0 * progress
            if ft.age >= ft.fade_start:
                fade_t = (ft.age - ft.fade_start) / max(1, ft.max_age - ft.fade_start)
                alpha  = int(255 * (1.0 - fade_t))
            else:
                alpha = 255
            font = self._bold_font(ft.font_size)
            s    = font.render(ft.text, True, ft.color)
            if alpha < 255:
                s = s.copy()
                s.set_alpha(alpha)
            surface.blit(s, s.get_rect(centerx=int(ft.x), centery=int(cur_y)))

    def _draw_status_panels(self, surface: pygame.Surface) -> None:
        # Player panel
        p_rect = pygame.Rect(0, _STATUS_Y, _W // 2 - 10, _STATUS_H)
        pygame.draw.rect(surface, _PANEL_BG, p_rect)
        pygame.draw.rect(surface, _DARK_BORDER, p_rect, 1)
        x0, y0 = p_rect.x + 12, p_rect.y + 10

        surface.blit(self._f_sub.render(self.player.name, True, _WHITE), (x0, y0))
        surface.blit(self._f_body.render(f"Gold: {self.player.gold}", True, _GOLD),
                     (x0 + 200, y0 + 4))
        self._draw_bar(surface, x0, y0 + 34, 280, 16, self.player.hp, self.player.max_hp, _RED, "HP")
        self._draw_bar(surface, x0, y0 + 58, 280, 16,
                       self.player.stamina, self.player.max_stamina, _BLUE, "STA")
        surface.blit(self._f_body.render(f"STR {self.player.strength}", True, (200, 95, 50)),
                     (x0, y0 + 84))
        surface.blit(self._f_body.render(f"AGI {self.player.agility}", True, (200, 175, 55)),
                     (x0 + 100, y0 + 84))
        self._draw_limb_grid(surface, x0, y0 + 110, self.player, self._player_limb_flash)

        # Enemy panel
        e_rect = pygame.Rect(_W // 2 + 10, _STATUS_Y, _W // 2 - 10, _STATUS_H)
        pygame.draw.rect(surface, _PANEL_BG, e_rect)
        pygame.draw.rect(surface, _DARK_BORDER, e_rect, 1)
        ex0, ey0 = e_rect.x + 12, e_rect.y + 10

        surface.blit(self._f_sub.render(self.enemy.name, True, (200, 80, 80)), (ex0, ey0))
        self._draw_bar(surface, ex0, ey0 + 34, 280, 16, self.enemy.hp, self.enemy.max_hp, _RED, "HP")
        self._draw_bar(surface, ex0, ey0 + 58, 280, 16,
                       self.enemy.stamina, self.enemy.max_stamina, _BLUE, "STA")
        wpn   = self.enemy.weapon.get("name", "?")
        grade = self.enemy.weapon.get("grade", "?")
        arm   = self.enemy.armor.get("type", "?") if self.enemy.armor else "None"
        for i, (txt, col) in enumerate([
            (f"Weapon: {wpn} ({grade})", _GRAY),
            (f"Armor:  {arm}",           _GRAY),
            (f"STR {self.enemy.strength}", (200, 95, 50)),
        ]):
            surface.blit(self._f_body.render(txt, True, col), (ex0, ey0 + 84 + i * 22))
        surface.blit(self._f_body.render(f"AGI {self.enemy.agility}", True, (200, 175, 55)),
                     (ex0 + 100, ey0 + 84 + 2 * 22))
        self._draw_limb_grid(surface, ex0, ey0 + 152, self.enemy, self._enemy_limb_flash)

    def _draw_bar(self, surface: pygame.Surface, x: int, y: int, w: int, h: int,
                  cur: int, mx: int, color: tuple, label: str) -> None:
        pct = max(0.0, cur / mx) if mx else 0.0
        pygame.draw.rect(surface, (35, 28, 20), (x, y, w, h))
        if pct > 0:
            pygame.draw.rect(surface, color, (x, y, int(w * pct), h))
        pygame.draw.rect(surface, _DARK_BORDER, (x, y, w, h), 1)
        surface.blit(self._f_small.render(f"{label} {cur}/{mx}", True, _WHITE), (x + 4, y + 1))

    def _draw_limb_grid(self, surface: pygame.Surface, x: int, y: int, entity,
                         flash: dict[str, int] | None = None) -> None:
        from ..systems.limb_system import LimbSystem
        box_w, box_h, gap = 62, 18, 4
        for i, limb in enumerate(LimbSystem.LIMBS):
            integrity = entity.limbs.get_integrity(limb) if entity.limbs else 100
            if flash and limb in flash:
                color = _RED
            elif integrity >= 60:
                color = _GREEN
            elif integrity > 0:
                color = _YELLOW
            else:
                color = _LIMB_DEAD
            bx = x + i * (box_w + gap)
            pygame.draw.rect(surface, color, (bx, y, box_w, box_h), border_radius=2)
            lbl = self._f_small.render(f"{limb[:5]} {integrity}", True, _DARK_BG)
            surface.blit(lbl, lbl.get_rect(center=(bx + box_w // 2, y + box_h // 2)))

    def _draw_action_menu(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (20, 15, 10), (0, _BUTTON_Y, _W, _BUTTON_H))
        pygame.draw.line(surface, _DARK_BORDER, (0, _BUTTON_Y), (_W, _BUTTON_Y), 1)

        self._action_btn_rects = {}
        self._retreat_btn_rect = None
        self._advance_btn_rect = None
        self._continue_rect    = None

        cy = _BUTTON_Y + _BUTTON_H // 2

        if self.state == "round_over":
            cont_rect = pygame.Rect(_W // 2 - 180, cy - 25, 360, 50)
            pygame.draw.rect(surface, (35, 28, 20), cont_rect, border_radius=6)
            pygame.draw.rect(surface, _DARK_BORDER, cont_rect, 2, border_radius=6)
            hint = self._f_sub.render("SPACE / click — continue", True, _GRAY)
            surface.blit(hint, hint.get_rect(center=cont_rect.center))
            self._continue_rect = cont_rect
            return

        if self.state == "battle_over":
            return

        # Move buttons
        ret_rect = pygame.Rect(_MOVE_BTN_MARGIN, cy - _MOVE_BTN_H // 2, _MOVE_BTN_W, _MOVE_BTN_H)
        adv_rect = pygame.Rect(_W - _MOVE_BTN_MARGIN - _MOVE_BTN_W, cy - _MOVE_BTN_H // 2,
                               _MOVE_BTN_W, _MOVE_BTN_H)
        for rect, label, arrow in ((ret_rect, "Retreat", "◀"), (adv_rect, "Advance", "▶")):
            pygame.draw.rect(surface, (30, 22, 14), rect, border_radius=6)
            pygame.draw.rect(surface, (80, 65, 40), rect, 2, border_radius=6)
            surface.blit(self._f_small.render(arrow, True, _GOLD),
                         self._f_small.render(arrow, True, _GOLD).get_rect(
                             center=(rect.centerx, rect.centery - 10)))
            surface.blit(self._f_small.render(label, True, _GRAY),
                         self._f_small.render(label, True, _GRAY).get_rect(
                             center=(rect.centerx, rect.centery + 10)))
        self._retreat_btn_rect = ret_rect
        self._advance_btn_rect = adv_rect

        # Action buttons
        available    = self.player.available_actions()
        weapon_acts  = (self.player.weapon.get("available_actions", ["Heavy", "Quick"])
                        if self.player.weapon else ["Heavy", "Quick"])
        actions      = [a for a in _ACTIONS_ORDER if a in weapon_acts or a == "Defend"]
        zone_x1      = ret_rect.right + 10
        zone_x2      = adv_rect.left  - 10
        total_w      = len(actions) * _BTN_W + (len(actions) - 1) * _BTN_GAP
        start_x      = zone_x1 + (zone_x2 - zone_x1 - total_w) // 2
        dist         = self._distance()

        for i, action in enumerate(actions):
            bx, by   = start_x + i * (_BTN_W + _BTN_GAP), cy - _BTN_H // 2
            enabled  = action in available
            warn     = action in ("Heavy", "Quick") and dist >= _RANGE_FAR
            ranged_w = action == "Ranged" and dist <= _RANGE_CLOSE

            if warn:
                bg, border, text_c = (25, 18, 12), (100, 60, 40), (100, 80, 60)
            elif ranged_w:
                bg, border, text_c = (35, 26, 16), (160, 140, 60), (200, 180, 80)
            else:
                bg     = (35, 26, 16) if enabled else (22, 18, 14)
                border = _GOLD if enabled else (55, 45, 35)
                text_c = _WHITE if enabled else (70, 65, 60)

            btn_rect = pygame.Rect(bx, by, _BTN_W, _BTN_H)
            pygame.draw.rect(surface, bg,     btn_rect, border_radius=6)
            pygame.draw.rect(surface, border, btn_rect, 2, border_radius=6)
            surface.blit(self._f_small.render(f"[{i + 1}]", True, _GOLD if enabled else _GRAY),
                         (bx + 8, by + 8))
            al = self._f_sub.render(action, True, text_c)
            surface.blit(al, al.get_rect(center=(bx + _BTN_W // 2, by + _BTN_H // 2 + 4)))
            if warn:
                ms = self._f_small.render("OUT OF RANGE", True, (180, 80, 40))
                surface.blit(ms, ms.get_rect(centerx=bx + _BTN_W // 2, bottom=by + _BTN_H - 4))
            self._action_btn_rects[action] = btn_rect

    def _draw_log_bar(self, surface: pygame.Surface) -> None:
        log_rect = pygame.Rect(0, _LOG_Y, _W, _LOG_H)
        pygame.draw.rect(surface, (12, 9, 6), log_rect)
        pygame.draw.line(surface, _DARK_BORDER, (0, _LOG_Y), (_W, _LOG_Y), 1)
        max_lines = max(1, _LOG_H // 18)
        for i, line in enumerate(self.log_lines[-max_lines:]):
            if "CRITICAL" in line:             color = (240, 160, 60)
            elif "destroyed" in line or "evades" in line: color = (220, 90, 70)
            elif "misses" in line or "penalty" in line:   color = (180, 130, 60)
            elif "advances" in line or "retreats" in line or "knocked" in line:
                                               color = (80, 140, 180)
            else:                              color = (160, 145, 110)
            surface.blit(self._f_hint.render(line, True, color),
                         (8, _LOG_Y + 4 + i * 18))

    def _draw_battle_over_banner(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((_W, _H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title_txt = "VICTORY" if self._victory else "DEFEATED"
        title_clr = (80, 220, 80) if self._victory else (220, 60, 60)
        sub_txt   = (f"+{self.enemy.gold_reward} gold"
                     if self._victory else "You have fallen in the arena.")

        cx, cy = _W // 2, _H // 2
        t = self._f_big.render(title_txt, True, title_clr)
        surface.blit(t, t.get_rect(center=(cx, cy - 60)))
        s = self._f_sub.render(sub_txt, True, _GRAY)
        surface.blit(s, s.get_rect(center=(cx, cy + 10)))
        h = self._f_hint.render("SPACE / click to continue", True, (100, 90, 70))
        surface.blit(h, h.get_rect(center=(cx, cy + 60)))

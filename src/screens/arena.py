from __future__ import annotations
import math
import os
import pygame
from typing import TYPE_CHECKING
from ._anim import (
    AnimSys, AState,
    quick_atk, heavy_atk, defend_anim,
    hit_flash, sprite_knockback, screen_shake,
    miss_flash, death_anim, screen_fade, hold_black, sound_at,
    boss_entry, screen_flash_white,
)
from ..systems.sound import SoundSystem
from ..systems.spritesheet import SpriteSheet
from ..systems.animation import AnimationController, IDLE, WALK, ATTACK, DEATH, HURT
from ..systems.enemy_appearance import EnemyAppearance

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..entities.enemy  import Enemy
    from ..systems.combat  import CombatResolver, RoundResult

_ASSETS  = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images")
_SOUNDS  = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sounds")
_PACK    = os.path.join(_ASSETS, "GandalfHardcore Character Asset Pack")

# Frame at which the weapon makes contact for each action (used for impact sounds)
_CONTACT_FRAME: dict[str, int] = {"Quick": 11, "Heavy": 15, "Ranged": 0}

# Player sprite layers (relative to _PACK) — all 800×448, 80×64 per frame, black colorkey
# Hair drawn FIRST (base); skin drawn on top so face pixels overwrite hair at face-center.
# Hair still shows at crown (y<22) and at sides where skin has no pixels.
_PLAYER_LAYERS: list[str] = [
    "Female Hair/Female Hair1.png",              # hair (base — drawn first)
    "Character skin colors/Female Skin2.png",    # skin/face on top (face visible)
    "Female Clothing/Blue Panties and Bra.png",  # clothing
    "Female Hand/Female Sword.png",              # weapon
]
# Enemy layers are generated per-stage by EnemyAppearance (not a constant)

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
_SPRITE_H    = 128   # scaled sprite height (64 × 2)

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
_HOVER       = (255, 230, 120)

# Button layout
_BTN_W, _BTN_H   = 155, 68
_BTN_GAP         = 12
_MOVE_BTN_W      = 120
_MOVE_BTN_H      = 68
_MOVE_BTN_MARGIN = 18
_ACTIONS_ORDER   = ["Heavy", "Quick", "Defend", "Ranged"]
_BLEED_DMG       = 20   # HP lost per turn when any limb is severed


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
        self._snd: SoundSystem | None = None  # created in _init_assets

        # Sprite animation controllers (created in _init_assets)
        self._player_anim: AnimationController | None = None
        self._enemy_anim:  AnimationController | None = None
        self._is_boss:     bool = EnemyAppearance().is_boss(player.stage)

        # Clickable rects (populated each draw)
        self._action_btn_rects: dict[str, pygame.Rect] = {}
        self._retreat_btn_rect: pygame.Rect | None     = None
        self._advance_btn_rect: pygame.Rect | None     = None
        self._continue_rect:    pygame.Rect | None     = None

        # Sound controls UI state
        self._sound_open:    bool           = False
        self._slider_drag:   bool           = False
        self._speaker_rect:  pygame.Rect | None = None
        self._mute_rect:     pygame.Rect | None = None
        self._slider_track:  pygame.Rect | None = None

        self._assets_ready = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._anim.tick()
        if self._player_anim:
            self._player_anim.update(dt)
        if self._enemy_anim:
            self._enemy_anim.update(dt)
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

        # Full-screen overlay (black fade or white flash)
        if st.overlay_alpha > 0:
            ov = pygame.Surface((_W, _H))
            ov.fill(st.overlay_color)
            ov.set_alpha(st.overlay_alpha)
            self.surface.blit(ov, (0, 0))

        # Sound controls (drawn on top, not affected by screen shake)
        if self._assets_ready:
            self._draw_sound_controls(self.surface)

    def handle_event(self, event: pygame.event.Event) -> None:
        # Sound controls — processed first, not blocked by animation lock
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self._speaker_rect and self._speaker_rect.collidepoint(pos):
                self._sound_open = not self._sound_open
                return
            if self._sound_open and self._snd:
                if self._mute_rect and self._mute_rect.collidepoint(pos):
                    self._snd.mute_music(not self._snd.music_muted)
                    return
                if self._slider_track and self._slider_track.collidepoint(pos):
                    rel = (pos[0] - self._slider_track.left) / max(1, self._slider_track.width)
                    self._snd.set_music_volume(max(0.0, min(1.0, rel)))
                    self._slider_drag = True
                    return
            # Clicking outside submenu closes it (without passing click to game)
            if self._sound_open:
                sub_rect = pygame.Rect(_W - 196, _TOP_BAR_H, 190, 95)
                if not sub_rect.collidepoint(pos):
                    self._sound_open = False
                    return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._slider_drag = False

        if event.type == pygame.MOUSEMOTION and self._slider_drag and self._slider_track and self._snd:
            rel = (event.pos[0] - self._slider_track.left) / max(1, self._slider_track.width)
            self._snd.set_music_volume(max(0.0, min(1.0, rel)))

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
                if self._snd: self._snd.stop_music()
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
                if self._snd: self._snd.stop_music()
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

    def _can_move(self) -> bool:
        """Return False if either player leg is severed (integrity 0)."""
        if not self.player.limbs:
            return True
        return (self.player.limbs.get_integrity("L-Leg") > 0 and
                self.player.limbs.get_integrity("R-Leg") > 0)

    def _has_broken_limb(self, entity) -> bool:
        if not entity.limbs:
            return False
        return any(entity.limbs.get_integrity(l) == 0
                   for l in entity.limbs.LIMBS)

    def _move_player(self, delta: int) -> None:
        if not self._can_move():
            return
        new = max(0, min(self._player_tile + delta, _ARENA_TILES - 1))
        if delta > 0 and new >= self._enemy_tile:
            new = self._enemy_tile - 1
        if new != self._player_tile:
            self._player_tile = new
            self.log_lines.append(
                f"{self.player.name} {'advances' if delta > 0 else 'retreats'}."
                f" Distance: {self._distance()}"
            )
            if self._snd:
                self._snd.play("movement")
            if self._player_anim:
                self._player_anim.trigger(WALK)
        self._enemy_action_on_move()

    def _enemy_action_on_move(self) -> None:
        """Enemy takes a free action while the player repositions."""
        enemy_action = self.enemy.choose_action(player_last_action=self._last_player_action)
        self.resolver.consume_stamina(self.enemy, enemy_action)

        dist       = self._distance()
        dmg_in     = 0
        is_crit    = False
        evaded     = False
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
                    evaded = True
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

        # Capture state for closures
        _dmg_in  = dmg_in
        _is_crit = is_crit
        _evaded  = evaded
        _snd     = self._snd
        floor_top = float(_ARENA_Y + _TILE_H - _SPRITE_H - 12)
        _atk  = {"Quick": quick_atk, "Heavy": heavy_atk, "Defend": defend_anim}
        _sw   = {"Quick": "swing_quick", "Heavy": "swing_heavy"}
        _cf_e = _CONTACT_FRAME.get(enemy_action, 0)

        def _phase_enemy_atk() -> None:
            if enemy_action in _atk:
                self._anim.add(_atk[enemy_action](False))
            if _snd and enemy_action in _sw:
                _n = _sw[enemy_action]
                self._anim.add(sound_at(lambda n=_n: _snd.play_swing(n), 0))

        def _phase_player_impact() -> None:
            if _dmg_in > 0:
                self._anim.add(hit_flash(True, _is_crit))
                self._anim.add(sprite_knockback(True, -30.0 if enemy_action == "Heavy" else -15.0))
                if enemy_action == "Heavy":
                    self._anim.add(screen_shake(10 if _is_crit else 5, 12))
                self._anim.float_text(
                    str(_dmg_in),
                    (255, 220, 50) if _is_crit else (255, 160, 100),
                    self._player_screen_cx(), floor_top,
                    36 if _is_crit else 28,
                )
                if _snd:
                    _imp = "impact_girl" if enemy_action == "Heavy" else "impact_quick"
                    self._anim.add(sound_at(lambda n=_imp: _snd.play_impact(n), _cf_e))
                    if _is_crit:
                        self._anim.add(sound_at(lambda: _snd.play("critical"), _cf_e))
            elif _evaded and _snd:
                self._anim.add(miss_flash(True))
                self._anim.float_text("MISS", _WHITE, self._player_screen_cx(), floor_top)
                self._anim.add(sound_at(lambda: _snd.play("miss"), _cf_e))

        def _on_done() -> None:
            if self._player_anim:
                self._player_anim.trigger(IDLE)
            self.log_lines.extend(pending)
            if not self.player.is_alive:
                self._victory = False
                if self._player_anim:
                    self._player_anim.trigger(DEATH)
                if self._snd:
                    self._snd.play("death")
                self._anim.add(death_anim(True), screen_fade())
                def _after_death() -> None:
                    self._anim.add(hold_black(120))
                    self._anim.on_done(lambda: setattr(self, "state", "battle_over"))
                self._anim.on_done(_after_death)

        self._run_phases([_phase_enemy_atk, _phase_player_impact], on_complete=_on_done)

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

    def _run_phases(self, phases: list, on_complete=None) -> None:
        """Run animation phases sequentially: each phase adds tracks, next starts when done."""
        if not phases:
            if on_complete:
                on_complete()
            return
        phases[0]()
        tail = phases[1:]
        self._anim.on_done(lambda t=tail, cb=on_complete: self._run_phases(t, cb))

    def _queue_combat_anims(self, player_action: str, enemy_action: str,
                             result: "RoundResult", on_complete=None) -> None:
        floor_top = float(_ARENA_Y + _TILE_H - _SPRITE_H - 12)
        snd  = self._snd
        _atk = {"Quick": quick_atk, "Heavy": heavy_atk, "Defend": defend_anim}
        _sw  = {"Quick": "swing_quick", "Heavy": "swing_heavy"}
        _cf_p = _CONTACT_FRAME.get(player_action, 0)
        _cf_e = _CONTACT_FRAME.get(enemy_action, 0)

        def _phase_player_atk() -> None:
            if player_action in _atk:
                self._anim.add(_atk[player_action](True))
            if self._player_anim and player_action in ("Quick", "Heavy"):
                self._player_anim.trigger(ATTACK)
            if snd and player_action in _sw:
                _n = _sw[player_action]
                self._anim.add(sound_at(lambda n=_n: snd.play_swing(n), 0))

        def _phase_enemy_impact() -> None:
            if result.player_damage_out > 0:
                crit = result.player_crit
                if self._enemy_anim:
                    self._enemy_anim.trigger(HURT)
                self._anim.add(hit_flash(False, crit))
                self._anim.add(sprite_knockback(False, +30.0 if player_action == "Heavy" else +15.0))
                if player_action == "Heavy":
                    self._anim.add(screen_shake(10 if crit else 5, 12))
                self._anim.float_text(
                    str(result.player_damage_out),
                    (255, 220, 50) if crit else _WHITE,
                    self._enemy_screen_cx(), floor_top,
                    36 if crit else 28,
                )
                if snd:
                    _imp = "impact_man" if player_action == "Heavy" else "impact_quick"
                    self._anim.add(sound_at(lambda n=_imp: snd.play_impact(n), _cf_p))
                    if crit:
                        self._anim.add(sound_at(lambda: snd.play("critical"), _cf_p))
            else:
                self._anim.add(miss_flash(False))
                self._anim.float_text("MISS", _WHITE, self._enemy_screen_cx(), floor_top)
                if snd:
                    self._anim.add(sound_at(lambda: snd.play("miss"), _cf_p))
            for limb in result.new_enemy_injuries:
                self._enemy_limb_flash[limb] = 20
                self._anim.float_text(f"{limb} INJURED!", (255, 130, 0),
                                       self._enemy_screen_cx(), floor_top - 22, 22)
            for limb in result.new_enemy_wounds:
                self._enemy_limb_flash[limb] = 20
                self._anim.float_text(f"{limb} SEVERED!", (255, 40, 40),
                                       self._enemy_screen_cx(), floor_top - 22, 22)
            if snd and (result.new_enemy_wounds or result.new_enemy_injuries):
                self._anim.add(sound_at(lambda: snd.play("limb_injury"), 0))

        def _phase_enemy_atk() -> None:
            if enemy_action in _atk:
                self._anim.add(_atk[enemy_action](False))
            if self._enemy_anim and enemy_action in ("Quick", "Heavy"):
                self._enemy_anim.trigger(ATTACK)
            if snd and enemy_action in _sw:
                _n = _sw[enemy_action]
                self._anim.add(sound_at(lambda n=_n: snd.play_swing(n), 0))

        def _phase_player_impact() -> None:
            if result.player_damage_in > 0:
                crit = result.enemy_crit
                if self._player_anim:
                    self._player_anim.trigger(HURT)
                self._anim.add(hit_flash(True, crit))
                self._anim.add(sprite_knockback(True, -30.0 if enemy_action == "Heavy" else -15.0))
                if enemy_action == "Heavy":
                    self._anim.add(screen_shake(10 if crit else 5, 12))
                self._anim.float_text(
                    str(result.player_damage_in),
                    (255, 220, 50) if crit else (255, 160, 100),
                    self._player_screen_cx(), floor_top,
                    36 if crit else 28,
                )
                if snd:
                    _imp = "impact_girl" if enemy_action == "Heavy" else "impact_quick"
                    self._anim.add(sound_at(lambda n=_imp: snd.play_impact(n), _cf_e))
                    if crit:
                        self._anim.add(sound_at(lambda: snd.play("critical"), _cf_e))
            else:
                self._anim.add(miss_flash(True))
                self._anim.float_text("MISS", _WHITE, self._player_screen_cx(), floor_top)
                if snd:
                    self._anim.add(sound_at(lambda: snd.play("miss"), _cf_e))
            for limb in result.new_player_injuries:
                self._player_limb_flash[limb] = 20
                self._anim.float_text(f"{limb} INJURED!", (255, 130, 0),
                                       self._player_screen_cx(), floor_top - 22, 22)
            for limb in result.new_player_wounds:
                self._player_limb_flash[limb] = 20
                self._anim.float_text(f"{limb} SEVERED!", (255, 40, 40),
                                       self._player_screen_cx(), floor_top - 22, 22)
            if snd and (result.new_player_wounds or result.new_player_injuries):
                self._anim.add(sound_at(lambda: snd.play("limb_injury"), 0))

        def _phase_neither() -> None:
            if player_action in _atk:
                self._anim.add(_atk[player_action](True))
            if enemy_action in _atk:
                self._anim.add(_atk[enemy_action](False))
            if snd and player_action == "Defend" and enemy_action == "Defend":
                self._anim.add(sound_at(lambda: snd.play("block"), 0))
            elif snd:
                # One side blocked — play block for whichever is defending
                if player_action == "Defend":
                    self._anim.add(sound_at(lambda: snd.play("block"), 0))
                elif enemy_action == "Defend":
                    self._anim.add(sound_at(lambda: snd.play("block"), 0))

        outcome = result.outcome
        if outcome == "attacker_hits":
            phases = [_phase_player_atk, _phase_enemy_impact, _phase_enemy_atk]
        elif outcome == "defender_hits":
            phases = [_phase_enemy_atk, _phase_player_impact, _phase_player_atk]
        elif outcome == "both_hit":
            phases = [_phase_player_atk, _phase_enemy_impact,
                      _phase_enemy_atk, _phase_player_impact]
        else:  # "neither"
            phases = [_phase_neither]

        self._run_phases(phases, on_complete)

    # ── Round handling ────────────────────────────────────────────────────────

    def _execute_round(self, player_action: str) -> None:
        self._move_enemy_ai()

        enemy_action = self.enemy.choose_action(player_last_action=self._last_player_action)
        self.enemy.record_player_action(player_action)
        self._last_player_action = player_action

        # ── Bleeding (any severed limb = 20 dmg/turn) ─────────────────────
        bleed_log: list[str] = []
        if self._has_broken_limb(self.player):
            bleed = self.player.take_damage(_BLEED_DMG)
            bleed_log.append(f"  {self.player.name} bleeds for {bleed} damage!")
        if self._has_broken_limb(self.enemy):
            bleed = self.enemy.take_damage(_BLEED_DMG)
            bleed_log.append(f"  {self.enemy.name} bleeds for {bleed} damage!")

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
        pending_log = bleed_log[:]
        pending_log.append(
            f"-- {self.player.name}: {player_action}  vs  {self.enemy.name}: {enemy_action} --"
        )
        pending_log.extend(result.log)

        def _on_done() -> None:
            self.log_lines.extend(pending_log)
            battle_end = self.resolver.is_battle_over(self.player, self.enemy)
            if battle_end:
                self._victory = (battle_end == "player_win")
                dying_player  = (battle_end == "enemy_win")
                if dying_player and self._player_anim:
                    self._player_anim.trigger(DEATH)
                elif not dying_player and self._enemy_anim:
                    self._enemy_anim.trigger(DEATH)
                if self._snd:
                    self._snd.play("death")
                self._anim.add(death_anim(dying_player), screen_fade())
                def _after_death() -> None:
                    self._anim.add(hold_black(120))
                    def _set_over() -> None:
                        if self.state == "battle_over":
                            return
                        self.state = "battle_over"
                        if self._snd and self._victory:
                            self._snd.play("victory")
                            self._snd.play("crowd_cheer", loops=2)
                    self._anim.on_done(_set_over)
                self._anim.on_done(_after_death)
            else:
                self.state = "round_over"

        self._queue_combat_anims(player_action, enemy_action, result, on_complete=_on_done)

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
        self._snd = SoundSystem(_SOUNDS)

        # Sprite animation controllers — load each layer; skip silently if missing
        def _load_layers(paths: list[str]) -> list[SpriteSheet]:
            sheets = []
            for rel in paths:
                s = SpriteSheet(os.path.join(_PACK, rel))
                if s.loaded:
                    sheets.append(s)
            return sheets

        p_layers = _load_layers(_PLAYER_LAYERS)
        if p_layers:
            self._player_anim = AnimationController(
                p_layers[0], flip=True, layers=p_layers[1:])

        # Enemy appearance — randomised per stage, boss-scaled
        _ea         = EnemyAppearance()
        e_rel_paths = _ea.generate_layers(self.player.stage)
        e_layers    = _load_layers(e_rel_paths)
        bscale      = _ea.get_boss_scale(self.player.stage)
        if e_layers:
            self._enemy_anim = AnimationController(
                e_layers[0], flip=False, layers=e_layers[1:], boss_scale=bscale)

        # Boss entry animation
        if self._is_boss:
            self._anim.add(boss_entry(30), screen_flash_white(10))

        self._bg_image: pygame.Surface | None = None
        try:
            raw = pygame.image.load(os.path.join(_ASSETS, "arena_bg_1.jpg")).convert()
            self._bg_image = pygame.transform.smoothscale(raw, (_W, _ARENA_H))
        except (pygame.error, FileNotFoundError):
            pass

        # Start background music
        if self._snd:
            self._snd.play_music(os.path.join(_SOUNDS, "arenamusic.mp3"))

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

        grade = self.enemy.weapon.get("grade", "?")
        if self._is_boss:
            name_surf = self._bold_font(38).render(
                f"⚔  {self.enemy.name}  ⚔", True, (240, 55, 55))
        else:
            name_surf = self._f_sub.render(
                f"{self.enemy.name}  [{grade} weapon]", True, (200, 80, 80))
        surface.blit(name_surf, name_surf.get_rect(centerx=_W // 2, centery=_TOP_BAR_H // 2))

        hp_pct   = self.enemy.hp / self.enemy.max_hp
        hp_color = _RED if hp_pct < 0.3 else _YELLOW if hp_pct < 0.6 else (_RED if self._is_boss else _GREEN)
        bar_w    = 260 if self._is_boss else 180
        bar_x    = _W - bar_w - 16
        bar_y    = (_TOP_BAR_H - 14) // 2
        pygame.draw.rect(surface, (40, 15, 15), (bar_x, bar_y, bar_w, 14), border_radius=3)
        pygame.draw.rect(surface, hp_color,     (bar_x, bar_y, int(bar_w * hp_pct), 14), border_radius=3)
        hp_txt = self._f_small.render(f"HP {self.enemy.hp}/{self.enemy.max_hp}", True, _WHITE)
        surface.blit(hp_txt, hp_txt.get_rect(centerx=bar_x + bar_w // 2, centery=bar_y + 7))

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

    def _draw_crown(self, surface: pygame.Surface, cx: int, tip_y: int) -> None:
        """Draw a small golden star crown above the boss sprite."""
        r_out, r_in = 10, 5
        pts = []
        for i in range(10):
            angle = math.pi / 2 - i * 2 * math.pi / 10  # start at top
            r     = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(angle), tip_y + r * math.sin(angle)))
        pygame.draw.polygon(surface, (255, 210, 40), pts)
        pygame.draw.polygon(surface, (200, 155, 20), pts, 1)

    def _draw_combatants(self, surface: pygame.Surface) -> None:
        st      = self._anim.state
        floor_y = _ARENA_Y + _TILE_H - 8

        # ── Player ────────────────────────────────────────────────────────
        px_base   = _ARENA_X + self._player_tile * _TILE_W + _TILE_W // 2
        px_center = px_base + int(st.player_atk_x + st.player_kb_x)

        if self._player_anim:
            spr        = self._player_anim.get_current_surface()
            p_tint     = (255, 255, 255, 180) if self._player_anim.state == HURT else st.player_tint
            spr_top    = self._apply_sprite(surface, spr,
                                            px_center, floor_y,
                                            st.player_angle, st.player_alpha, p_tint)
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

        if self._enemy_anim:
            espr      = self._enemy_anim.get_current_surface()
            e_tint    = (255, 255, 255, 180) if self._enemy_anim.state == HURT else st.enemy_tint
            angle     = -st.enemy_angle if st.enemy_angle else 0

            # Boss: red danger aura behind sprite
            if self._is_boss:
                aw, ah = espr.get_width(), espr.get_height()
                ax, ay = ex_center - aw // 2 - 6, floor_y - ah - 6
                pulse  = int(40 + 20 * abs(((self._anim.state.screen_dx or 0) * 13) % 60 - 30) / 30)
                pygame.draw.rect(surface, (140, 20 + pulse, 20 + pulse),
                                 (ax, ay, aw + 12, ah + 12), 3, border_radius=6)

            ename_top = self._apply_sprite(surface, espr,
                                           ex_center, floor_y,
                                           angle, st.enemy_alpha, e_tint)

            # Boss: star crown above head
            if self._is_boss:
                self._draw_crown(surface, ex_center, ename_top - 6)
        else:
            erx = ex_center - 28
            ery = floor_y - 100
            pygame.draw.rect(surface, (200, 50, 40), (erx, ery, 56, 100), border_radius=4)
            ename_top = ery

        name_col = (220, 60, 60) if self._is_boss else _WHITE
        ename = self._f_small.render(self.enemy.name[:10], True, name_col)
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
        p_melee  = self.player.weapon
        p_ranged = self.player.ranged_weapon
        wpn_txt  = (p_melee.get("name", "?") if p_melee else "—") + (
                   f"  /  {p_ranged.get('name','?')}" if p_ranged else "")
        surface.blit(self._f_body.render(f"Wpn: {wpn_txt[:28]}", True, _GRAY), (x0, y0 + 84))
        surface.blit(self._f_body.render(f"STR {self.player.strength}", True, (200, 95, 50)),
                     (x0, y0 + 106))
        surface.blit(self._f_body.render(f"AGI {self.player.agility}", True, (200, 175, 55)),
                     (x0 + 100, y0 + 106))
        self._draw_limb_grid(surface, x0, y0 + 130, self.player, self._player_limb_flash)

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
            elif integrity > 50:
                color = _GREEN
            elif integrity > 0:
                color = _YELLOW   # injured
            else:
                color = _LIMB_DEAD  # severed
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
        mouse_pos  = pygame.mouse.get_pos()
        can_move   = self._can_move()
        for rect, label, arrow in ((ret_rect, "Retreat", "◀"), (adv_rect, "Advance", "▶")):
            hov = rect.collidepoint(mouse_pos) and can_move
            if can_move:
                bg_c  = (45, 34, 20) if hov else (35, 26, 15)
                bd_c  = _HOVER if hov else (160, 125, 60)
                arr_c = _HOVER if hov else _GOLD
                lbl_c = _HOVER if hov else _WHITE
            else:
                bg_c, bd_c, arr_c, lbl_c = (20, 16, 12), (55, 45, 35), (70, 60, 45), (60, 55, 45)
            pygame.draw.rect(surface, bg_c, rect, border_radius=6)
            pygame.draw.rect(surface, bd_c, rect, 2, border_radius=6)
            surface.blit(self._f_sub.render(arrow, True, arr_c),
                         self._f_sub.render(arrow, True, arr_c).get_rect(
                             center=(rect.centerx, rect.centery - 10)))
            surface.blit(self._f_small.render(label, True, lbl_c),
                         self._f_small.render(label, True, lbl_c).get_rect(
                             center=(rect.centerx, rect.centery + 12)))
        if not can_move:
            imm = self._f_small.render("IMMOBILIZED", True, (180, 60, 60))
            mid = (ret_rect.right + adv_rect.left) // 2
            surface.blit(imm, imm.get_rect(centerx=mid, bottom=ret_rect.top - 2))
        self._retreat_btn_rect = ret_rect
        self._advance_btn_rect = adv_rect

        # Action buttons — show exactly what the player can do this round
        available = self.player.available_actions()
        actions   = [a for a in _ACTIONS_ORDER if a in available]
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

    def _draw_sound_controls(self, surface: pygame.Surface) -> None:
        """Draw speaker icon + optional submenu in the top-right corner."""
        # ── Speaker button ────────────────────────────────────────────────
        btn = pygame.Rect(_W - 46, 5, 40, 40)
        self._speaker_rect = btn
        mouse = pygame.mouse.get_pos()
        hov   = btn.collidepoint(mouse)
        muted = self._snd.music_muted if self._snd else False

        pygame.draw.rect(surface, (45, 35, 20) if hov else (25, 18, 10), btn, border_radius=6)
        pygame.draw.rect(surface, _GOLD if hov else (90, 72, 40), btn, 1, border_radius=6)

        # Speaker icon geometry (relative to btn center)
        cx, cy = btn.centerx, btn.centery
        col = (210, 175, 80) if hov else (160, 130, 55)
        # Body rectangle
        pygame.draw.rect(surface, col, (cx - 9, cy - 4, 5, 8))
        # Cone polygon
        pygame.draw.polygon(surface, col, [
            (cx - 4, cy - 5), (cx + 3, cy - 9), (cx + 3, cy + 9), (cx - 4, cy + 5)
        ])
        if muted:
            pygame.draw.line(surface, (220, 60, 60), (cx + 4, cy - 6), (cx + 10, cy + 6), 2)
            pygame.draw.line(surface, (220, 60, 60), (cx + 10, cy - 6), (cx + 4, cy + 6), 2)
        else:
            # Two sound-wave arcs
            for r in (5, 9):
                pygame.draw.arc(surface, col,
                                (cx + 3, cy - r, r, r * 2), -0.65, 0.65, 2)

        if not self._sound_open:
            return

        # ── Submenu panel ─────────────────────────────────────────────────
        panel = pygame.Rect(_W - 196, _TOP_BAR_H, 190, 95)
        pygame.draw.rect(surface, (28, 20, 12), panel, border_radius=6)
        pygame.draw.rect(surface, (80, 65, 40), panel, 1, border_radius=6)

        px, py = panel.x + 10, panel.y + 10
        vol    = self._snd.music_volume if self._snd else 0.7

        # Volume label
        surface.blit(self._f_small.render("Music Volume", True, _GRAY), (px, py))

        # Slider track
        track = pygame.Rect(px, py + 18, 150, 6)
        self._slider_track = track
        pygame.draw.rect(surface, (55, 42, 26), track, border_radius=3)
        fill_w = int(track.width * vol)
        if fill_w > 0:
            pygame.draw.rect(surface, _GOLD,
                             (track.x, track.y, fill_w, track.height), border_radius=3)
        pygame.draw.rect(surface, (100, 80, 45), track, 1, border_radius=3)

        # Slider handle
        hx = track.x + fill_w
        pygame.draw.circle(surface, _GOLD, (hx, track.centery), 6)
        pygame.draw.circle(surface, (200, 155, 30), (hx, track.centery), 6, 1)

        # Volume percentage
        pct_txt = self._f_small.render(f"{int(vol * 100)}%", True, _WHITE)
        surface.blit(pct_txt, (track.right + 6, track.y - 2))

        # Mute checkbox
        mute_rect = pygame.Rect(px, py + 34, 14, 14)
        self._mute_rect = mute_rect
        pygame.draw.rect(surface, (55, 42, 26), mute_rect, border_radius=2)
        if muted:
            pygame.draw.rect(surface, _GOLD, mute_rect.inflate(-2, -2), border_radius=2)
        pygame.draw.rect(surface, (100, 80, 45), mute_rect, 1, border_radius=2)
        lbl = self._f_small.render("Mute", True, _GOLD if muted else _GRAY)
        surface.blit(lbl, (px + 18, py + 34))

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

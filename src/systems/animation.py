"""Sprite animation controller for arena characters.

States
------
IDLE   — row 0, 5 frames, loops at 8 fps
WALK   — row 1, 8 frames, loops at 10 fps
ATTACK — row 5, 6 frames, plays once then returns to IDLE at 12 fps
DEATH  — row 6, 10 frames, plays once then freezes on last frame at 8 fps
HURT   — no sheet row; overlays white tint for 3 ticks, then restores prior state

Usage::

    sheet  = SpriteSheet(path)
    ctrl   = AnimationController(sheet, flip=True)
    ctrl.trigger(ATTACK)
    ctrl.update(dt)
    surf   = ctrl.get_current_surface()   # 160×128, ready to blit
"""
from __future__ import annotations
import pygame
from .spritesheet import SpriteSheet, FRAME_W, FRAME_H

# ── State constants ──────────────────────────────────────────────────────────
IDLE   = "idle"
WALK   = "walk"
ATTACK = "attack"
DEATH  = "death"
HURT   = "hurt"

# (sheet_row, frame_count, fps, loops, next_state_when_done)
_ANIM_DEF: dict[str, tuple] = {
    IDLE:   (0,  5,  8.0,  True,  None),
    WALK:   (1,  8,  10.0, True,  None),
    ATTACK: (5,  6,  12.0, False, IDLE),
    DEATH:  (6,  10, 8.0,  False, None),   # freeze last frame
}

_SCALE      = 2    # 80×64 → 160×128
_HURT_TICKS = 3    # game ticks (≈3 frames @60 fps) for white flash


class AnimationController:
    """Manages animation state and produces per-frame surfaces for one character."""

    def __init__(
        self,
        sheet:      SpriteSheet,
        flip:       bool        = False,
        layers:     list[SpriteSheet] | None = None,
        boss_scale: float       = 1.0,
    ) -> None:
        self._sheet      = sheet
        self._flip       = flip
        self._layers     = layers or []
        self._boss_scale = boss_scale

        # Preload all animation strips
        self._frames: dict[str, list[pygame.Surface]] = {}
        for state, (row, count, *_) in _ANIM_DEF.items():
            self._frames[state] = sheet.get_animation(row, count)

        self._state:      str   = IDLE
        self._prev_state: str   = IDLE
        self._frame_idx:  int   = 0
        self._timer:      float = 0.0   # time accumulator (seconds)
        self._hurt_left:  int   = 0     # ticks remaining in HURT
        self._frozen:     bool  = False  # True after DEATH reaches last frame

    # ── Public API ───────────────────────────────────────────────────────────

    def trigger(self, state: str) -> None:
        """Request a state transition.  HURT preserves the current frame."""
        if state == HURT:
            # Record what we were doing so we can return after the flash
            if self._state != HURT:
                self._prev_state = self._state
            self._hurt_left  = _HURT_TICKS
            self._state      = HURT
            return

        if state == DEATH and self._state == DEATH:
            return  # already in death — don't restart

        self._state      = state
        self._frame_idx  = 0
        self._timer      = 0.0
        self._frozen     = False
        self._hurt_left  = 0

    def update(self, dt: float) -> None:
        """Advance the animation by dt seconds (called once per game tick)."""
        if self._state == HURT:
            self._hurt_left -= 1
            if self._hurt_left <= 0:
                # Restore the state we interrupted
                self._state = self._prev_state
            return

        if self._frozen:
            return

        cfg = _ANIM_DEF.get(self._state)
        if cfg is None:
            return

        _row, count, fps, loops, next_state = cfg
        self._timer += dt
        frame_dur = 1.0 / fps

        while self._timer >= frame_dur:
            self._timer -= frame_dur
            self._frame_idx += 1
            if self._frame_idx >= count:
                if loops:
                    self._frame_idx = 0
                elif next_state:
                    self._state     = next_state
                    self._frame_idx = 0
                    self._timer     = 0.0
                    break
                else:
                    # Freeze on last frame (DEATH)
                    self._frame_idx = count - 1
                    self._frozen    = True
                    break

    def get_current_surface(self) -> pygame.Surface:
        """Return the current frame as a 160×128 surface, flipped/composited.

        Compositing order:
        1. Composite base + all layers at native 80×64 (one blit per layer)
        2. Scale the composite 2× once
        3. Flip horizontally if flip=True (enemy facing left)
        """
        display_state = self._prev_state if self._state == HURT else self._state
        row, count, *_ = _ANIM_DEF.get(display_state, _ANIM_DEF[IDLE])
        frame_idx = min(self._frame_idx, count - 1)

        # ── 1. Build composite at native 80×64 ──────────────────────────────
        composite = pygame.Surface((FRAME_W, FRAME_H))
        composite.set_colorkey((0, 0, 0), pygame.RLEACCEL)

        base_frames = self._frames.get(display_state, self._frames[IDLE])
        composite.blit(base_frames[frame_idx], (0, 0))

        for layer in self._layers:
            composite.blit(layer.get_frame(row, frame_idx), (0, 0))

        # ── 2. Scale (2× base × boss_scale) ────────────────────────────────
        out_w  = int(FRAME_W * _SCALE * self._boss_scale)
        out_h  = int(FRAME_H * _SCALE * self._boss_scale)
        scaled = pygame.transform.scale(composite, (out_w, out_h))

        # ── 3. Flip for enemy ────────────────────────────────────────────────
        if self._flip:
            scaled = pygame.transform.flip(scaled, True, False)

        return scaled

    @property
    def state(self) -> str:
        return self._state

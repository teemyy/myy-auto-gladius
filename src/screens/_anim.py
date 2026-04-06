"""Arena animation primitives — parallel tracks, per-frame state, floating texts."""
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Callable


# ── Per-frame render state ────────────────────────────────────────────────────

@dataclass
class AState:
    """Reset to defaults at the start of every tick; each track writes its slice."""
    player_atk_x:  float        = 0.0   # lunge offset (px, + = right)
    enemy_atk_x:   float        = 0.0   # lunge offset (px, - = left toward player)
    player_kb_x:   float        = 0.0   # knockback offset (px)
    enemy_kb_x:    float        = 0.0
    player_tint:   tuple | None = None   # (R,G,B,A) overlay on sprite
    enemy_tint:    tuple | None = None
    screen_dx:     int          = 0      # shake offset
    screen_dy:     int          = 0
    player_angle:  float        = 0.0   # clockwise degrees (death rotation)
    enemy_angle:   float        = 0.0
    player_alpha:  int          = 255   # overall sprite opacity
    enemy_alpha:   int          = 255
    overlay_alpha: int          = 0     # full-screen black fade


@dataclass
class _FloatText:
    text:       str
    color:      tuple
    x:          float
    y:          float
    font_size:  int = 28
    age:        int = 0
    max_age:    int = 40
    fade_start: int = 25


# ── Core primitives ───────────────────────────────────────────────────────────

class _Seg:
    """One segment: calls fn(frame, AState) for dur frames."""
    __slots__ = ("dur", "fn", "_f")

    def __init__(self, dur: int, fn: Callable[[int, AState], None]) -> None:
        self.dur = dur
        self.fn  = fn
        self._f  = 0

    def tick(self, st: AState) -> bool:
        self.fn(self._f, st)
        self._f += 1
        return self._f >= self.dur


class _Track:
    """Sequential list of _Seg objects."""
    __slots__ = ("_segs", "_i")

    def __init__(self, segs: list[_Seg]) -> None:
        self._segs = segs
        self._i    = 0

    def tick(self, st: AState) -> bool:
        if self._i >= len(self._segs):
            return True
        if self._segs[self._i].tick(st):
            self._i += 1
        return self._i >= len(self._segs)


# ── Animation system ──────────────────────────────────────────────────────────

class AnimSys:
    """Runs parallel tracks each frame; fires callbacks when all finish."""

    def __init__(self) -> None:
        self._tracks:  list[_Track]     = []
        self._on_done: list[Callable]   = []
        self._ft:      list[_FloatText] = []
        self.state:    AState           = AState()

    def busy(self) -> bool:
        return bool(self._tracks)

    def tick(self) -> None:
        self.state   = AState()
        self._tracks = [t for t in self._tracks if not t.tick(self.state)]
        for ft in self._ft:
            ft.age += 1
        self._ft = [ft for ft in self._ft if ft.age < ft.max_age]
        if not self._tracks and self._on_done:
            cbs, self._on_done = self._on_done[:], []
            for cb in cbs:
                cb()

    def add(self, *tracks: _Track) -> "AnimSys":
        """Add one or more parallel tracks."""
        self._tracks.extend(tracks)
        return self

    def on_done(self, fn: Callable) -> "AnimSys":
        """Register callback for when all current tracks finish.
        Called immediately if no tracks are running."""
        if not self._tracks:
            fn()
        else:
            self._on_done.append(fn)
        return self

    def float_text(self, text: str, color: tuple, x: float, y: float,
                   font_size: int = 28) -> None:
        self._ft.append(_FloatText(text, color, x, y, font_size))

    def clear(self) -> None:
        self._tracks.clear()
        self._on_done.clear()
        # keep _ft so active floats finish naturally


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


# ── Animation factories ───────────────────────────────────────────────────────

def quick_atk(is_player: bool) -> _Track:
    """Lunge 80 px toward opponent (6 f), hold (3 f), snap back (4 f)."""
    d = +1 if is_player else -1
    def fn(f: int, st: AState) -> None:
        if f < 6:   v = 80.0 * f / 5
        elif f < 9: v = 80.0
        else:       v = 80.0 * (1.0 - (f - 9) / 3.0)
        if is_player: st.player_atk_x = d * v
        else:          st.enemy_atk_x  = d * v
    return _Track([_Seg(13, fn)])


def heavy_atk(is_player: bool) -> _Track:
    """Wind back 20 px (4 f), lunge 100 px (4 f), snap back (6 f)."""
    d = +1 if is_player else -1
    def fn(f: int, st: AState) -> None:
        if f < 4:   v = _lerp(0.0,   -20.0, f / 3.0)
        elif f < 8: v = _lerp(-20.0, 100.0, (f - 4) / 3.0)
        else:       v = _lerp(100.0,   0.0, (f - 8) / 5.0)
        if is_player: st.player_atk_x = d * v
        else:          st.enemy_atk_x  = d * v
    return _Track([_Seg(14, fn)])


def defend_anim(is_player: bool) -> _Track:
    """Slide 15 px backward with blue tint (8 f)."""
    d = +1 if is_player else -1
    def fn(f: int, st: AState) -> None:
        t = min(f / 2.0, 1.0)
        if is_player:
            st.player_atk_x = d * (-15.0 * t)
            st.player_tint  = (80, 120, 220, int(100 * t))
        else:
            st.enemy_atk_x = d * (-15.0 * t)
    return _Track([_Seg(8, fn)])


def hit_flash(is_player: bool, crit: bool) -> _Track:
    """Flash white (or red on crit) for 2 frames."""
    col = (255, 60, 60) if crit else (255, 255, 255)
    def fn(f: int, st: AState) -> None:
        if f < 2:
            tint = col + (200,)
            if is_player: st.player_tint = tint
            else:          st.enemy_tint  = tint
    return _Track([_Seg(4, fn)])


def sprite_knockback(is_player: bool, dx: float) -> _Track:
    """Push sprite dx pixels, decay to 0 over 6 f. +dx = rightward."""
    def fn(f: int, st: AState) -> None:
        v = dx * max(0.0, 1.0 - f / 5.0)
        if is_player: st.player_kb_x = v
        else:          st.enemy_kb_x  = v
    return _Track([_Seg(6, fn)])


def screen_shake(strength: int, frames: int) -> _Track:
    """Random ±strength pixel screen offset each frame."""
    offs = [(random.randint(-strength, strength),
             random.randint(-strength, strength)) for _ in range(frames)]
    def fn(f: int, st: AState) -> None:
        if f < len(offs):
            st.screen_dx, st.screen_dy = offs[f]
    return _Track([_Seg(frames, fn)])


def miss_flash(is_player: bool) -> _Track:
    """Dim to 50 % alpha then restore over 8 f."""
    def fn(f: int, st: AState) -> None:
        alpha = 128 if f < 4 else int(128 + 127 * (f - 4) / 3.0)
        if is_player: st.player_alpha = alpha
        else:          st.enemy_alpha  = alpha
    return _Track([_Seg(8, fn)])


def death_anim(is_player: bool) -> _Track:
    """Rotate 90° and fade to 0 alpha over 20 f."""
    def fn(f: int, st: AState) -> None:
        t = f / 19.0
        if is_player:
            st.player_angle = 90.0 * t
            st.player_alpha = int(255 * (1.0 - t))
        else:
            st.enemy_angle = 90.0 * t
            st.enemy_alpha = int(255 * (1.0 - t))
    return _Track([_Seg(20, fn)])


def screen_fade() -> _Track:
    """Fade entire screen to black over 20 f."""
    def fn(f: int, st: AState) -> None:
        st.overlay_alpha = int(255.0 * f / 19.0)
    return _Track([_Seg(20, fn)])


def hold_black(frames: int) -> _Track:
    """Hold a fully black overlay for the given number of frames."""
    def fn(f: int, st: AState) -> None:
        st.overlay_alpha = 255
    return _Track([_Seg(frames, fn)])


def sound_at(callback: Callable[[], None], frame: int = 0) -> _Track:
    """Fire callback exactly once at the given animation frame.

    The track completes after frame+1 ticks, so it never blocks other tracks
    from finishing.  Use this to tie sound triggers to specific animation frames.
    """
    def fn(f: int, _st: AState) -> None:
        if f == frame:
            callback()
    return _Track([_Seg(frame + 1, fn)])

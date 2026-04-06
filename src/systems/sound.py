"""Sound system for arena combat.

Load all WAV files once at startup; fail silently with a log warning for any
missing file.  All playback methods are no-ops when a sound is unavailable,
so gameplay is never interrupted by missing assets.

Usage::

    snd = SoundSystem(sounds_dir)
    snd.play("block")
    snd.play_swing("swing_quick")   # tracked so impact can cancel it
    snd.play_impact("impact_quick") # stops active swing first
    snd.set_master_volume(0.5)
"""
from __future__ import annotations
import logging
import os
import pygame

MASTER_VOLUME: float = 0.7

_FILES: dict[str, str] = {
    "swing_quick":  "swing_quick.wav",
    "swing_heavy":  "swing_heavy.wav",
    "impact_quick": "impact_quick.wav",
    "impact_heavy": "impact_heavy.wav",
    "impact_girl":  "impact_girl.wav",
    "impact_man":   "impact_man.wav",
    "movement":     "movement.wav",
    "block":        "block.wav",
    "miss":         "miss.wav",
    "critical":     "critical.wav",
    "limb_injury":  "limb_injury.wav",
    "death":        "death.wav",
    "victory":      "victory.wav",
    "crowd_cheer":  "crowd_cheer.wav",
}


class SoundSystem:
    """Loads and plays arena sound effects via pygame.mixer."""

    def __init__(self, sounds_dir: str,
                 master_volume: float = MASTER_VOLUME) -> None:
        self._sounds:   dict[str, pygame.mixer.Sound] = {}
        self._swing_ch: pygame.mixer.Channel | None   = None
        self._master    = max(0.0, min(1.0, master_volume))
        self._load_all(sounds_dir)

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load_all(self, sounds_dir: str) -> None:
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except pygame.error as exc:
                logging.warning("SoundSystem: mixer init failed (%s) — no audio.", exc)
                return
        for name, fname in _FILES.items():
            path = os.path.join(sounds_dir, fname)
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(self._master)
                self._sounds[name] = snd
            except (pygame.error, FileNotFoundError, OSError):
                logging.warning("Sound missing: %s", path)

    # ── Playback ──────────────────────────────────────────────────────────────

    def play(self, name: str, loops: int = 0) -> "pygame.mixer.Channel | None":
        """Play a sound by name; returns the channel or None if unavailable."""
        snd = self._sounds.get(name)
        if snd:
            try:
                return snd.play(loops=loops)
            except pygame.error:
                pass
        return None

    def stop(self, name: str) -> None:
        """Stop all instances of a named sound."""
        snd = self._sounds.get(name)
        if snd:
            try:
                snd.stop()
            except pygame.error:
                pass

    def play_swing(self, name: str) -> None:
        """Play a swing sound on the tracked channel so impact can cancel it."""
        self._swing_ch = self.play(name)

    def play_impact(self, name: str) -> None:
        """Cancel any active swing sound, then play the impact sound."""
        if self._swing_ch is not None:
            try:
                self._swing_ch.stop()
            except (pygame.error, AttributeError):
                pass
            self._swing_ch = None
        self.play(name)

    # ── Volume ────────────────────────────────────────────────────────────────

    def set_master_volume(self, volume: float) -> None:
        """Set master volume (0.0 – 1.0) and apply to every loaded sound."""
        self._master = max(0.0, min(1.0, volume))
        for snd in self._sounds.values():
            try:
                snd.set_volume(self._master)
            except pygame.error:
                pass

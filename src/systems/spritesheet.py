"""Sprite sheet loader for the GandalfHardcore character asset pack.

All sheets share the same 80×64-pixel frame grid:
    Row 0 — Idle   (5 frames)
    Row 1 — Walk   (8 frames)
    Row 2 — Run    (8 frames)
    Row 3 — Jump   (4 frames)
    Row 4 — Fall   (4 frames)
    Row 5 — Attack (6 frames)
    Row 6 — Death  (10 frames)
"""
from __future__ import annotations
import logging
import pygame

FRAME_W = 80
FRAME_H = 64


class SpriteSheet:
    """Loads a sprite sheet and slices it into individual frame surfaces."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._sheet: pygame.Surface | None = None
        try:
            raw = pygame.image.load(path).convert()
            raw.set_colorkey((0, 0, 0), pygame.RLEACCEL)
            self._sheet = raw
        except (pygame.error, FileNotFoundError, OSError):
            logging.warning("SpriteSheet: could not load %s", path)

    @property
    def loaded(self) -> bool:
        return self._sheet is not None

    def get_frame(self, row: int, col: int) -> pygame.Surface:
        """Return a single 80×64 surface from (row, col). Transparent background."""
        surf = pygame.Surface((FRAME_W, FRAME_H))
        surf.set_colorkey((0, 0, 0), pygame.RLEACCEL)
        if self._sheet:
            surf.blit(self._sheet, (0, 0),
                      pygame.Rect(col * FRAME_W, row * FRAME_H, FRAME_W, FRAME_H))
        return surf

    def get_animation(self, row: int, frame_count: int) -> list[pygame.Surface]:
        """Return a list of frame surfaces for the given row."""
        return [self.get_frame(row, col) for col in range(frame_count)]

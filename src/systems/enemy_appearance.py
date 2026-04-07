"""Generates randomised layer lists for enemy sprites.

Uses the stage number as a seed so appearance is deterministic across sessions.
"""
from __future__ import annotations
import logging
import os
import random

_PACK = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images",
                 "GandalfHardcore Character Asset Pack")
)

_BASE_SKIN = "Character skin colors/Male Skin2.png"
_HAIR      = "Male Hair/Male Hair5.png"
_WEAPON    = "Male Hand/Male Sword.png"

_PANTS: list[str] = [
    "Male Clothing/Blue Pants.png",
    "Male Clothing/Green Pants.png",
    "Male Clothing/Orange Pants.png",
    "Male Clothing/Pants.png",
    "Male Clothing/Purple Pants.png",
]
_SHIRTS: list[str] = [
    "Male Clothing/Blue Shirt v2.png",
    "Male Clothing/Green Shirt v2.png",
    "Male Clothing/orange Shirt v2.png",
    "Male Clothing/Purple Shirt v2.png",
    "Male Clothing/Shirt v2.png",
    "Male Clothing/Shirt.png",
]
_UNDERWEAR: list[str] = [
    "Male Clothing/Green Underwear.png",
    "Male Clothing/Orange Underwear.png",
    "Male Clothing/Purple Underwear.png",
    "Male Clothing/Red Underwear.png",
    "Male Clothing/Skyblue Underwear.png",
    "Male Clothing/Underwear.png",
]
_FEET: list[str] = [
    "Male Clothing/Boots.png",
    "Male Clothing/Shoes.png",
]

_BOSS_STAGES: set[int] = {4, 8, 12}
_BOSS_SCALE:  dict[int, float] = {4: 1.5, 8: 1.75, 12: 2.0}


class EnemyAppearance:
    """Deterministic enemy clothing generator."""

    def generate_layers(self, stage: int) -> list[str]:
        """Return ordered relative layer paths (bottom → top) for the given stage.

        Paths are relative to the GandalfHardcore Character Asset Pack root.
        Missing files are logged and skipped.
        """
        rng = random.Random(stage)

        # Stages 1-3: underwear only; 4+: full shirt
        top_pool = _UNDERWEAR if stage <= 3 else _SHIRTS

        candidates = [
            _BASE_SKIN,
            rng.choice(_FEET),
            rng.choice(_PANTS),
            rng.choice(top_pool),
            _HAIR,
            _WEAPON,
        ]

        layers: list[str] = []
        for rel in candidates:
            path = os.path.join(_PACK, rel)
            if os.path.isfile(path):
                layers.append(rel)
            else:
                logging.warning("EnemyAppearance: missing file: %s", path)
        return layers

    def get_boss_scale(self, stage: int) -> float:
        """Return extra scale multiplier for boss stages (1.0 for normal enemies)."""
        return _BOSS_SCALE.get(stage, 1.0)

    def is_boss(self, stage: int) -> bool:
        return stage in _BOSS_STAGES

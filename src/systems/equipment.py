from __future__ import annotations
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


class EquipmentSystem:
    """Loads and queries weapon and armor data from JSON.

    All item data is read once at startup and cached.  Python code never
    hardcodes stat numbers — always read through this system.
    """

    GRADES      = ("Iron", "Steel", "Mithril", "Adamantite", "Draconic")
    ARMOR_TYPES = ("Cloth", "Leather", "Scale", "Chainmail", "Plate")

    def __init__(self):
        self._weapons: list[dict] = []
        self._armors:  list[dict] = []

    # ── Loading ──────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Read weapons.json and armors.json into memory.  Call once at startup."""
        pass

    # ── Lookup ───────────────────────────────────────────────────────────────

    def get_weapon(self, weapon_id: str) -> dict:
        """Return the weapon data dict for the given id.  Raises KeyError if missing."""
        pass

    def get_armor(self, armor_id: str) -> dict:
        """Return the armor data dict for the given id.  Raises KeyError if missing."""
        pass

    def weapons_by_grade(self, grade: str) -> list[dict]:
        """Return all weapons of the given grade."""
        pass

    def armors_by_type(self, armor_type: str) -> list[dict]:
        """Return all armors of the given type."""
        pass

    # ── Grade helpers ────────────────────────────────────────────────────────

    def grade_level(self, grade: str) -> int:
        """Return the 1-based index of grade in GRADES (Iron=1 … Draconic=5)."""
        pass

    def next_grade(self, grade: str) -> str | None:
        """Return the next upgrade grade, or None if already Draconic."""
        pass

    def upgrade_cost(self, weapon: dict) -> int | None:
        """Return the gold cost to upgrade weapon to the next grade.

        Returns None if the weapon is already Draconic.
        Cost formula: base_price × 1.5 × (current_grade_level).
        """
        pass

    # ── Shop helpers ─────────────────────────────────────────────────────────

    def available_shop_weapons(self, max_grade: str) -> list[dict]:
        """Return all weapons with grade_level <= max_grade level.

        Used to populate the Smithy's stock at a given stage.
        """
        pass

    def available_shop_armors(self) -> list[dict]:
        """Return all armors (all types available in the Store at all times)."""
        pass

    def sell_price(self, item: dict) -> int:
        """Return 50 % of the item's buy price, rounded down."""
        pass

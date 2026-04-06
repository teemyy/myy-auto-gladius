from __future__ import annotations
import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Rarity weights for shop stock generation (lower grade = more common)
_GRADE_WEIGHTS = {1: 40, 2: 28, 3: 16, 4: 10, 5: 6}


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
        with open(DATA_DIR / "weapons.json", encoding="utf-8") as f:
            self._weapons = json.load(f)["weapons"]
        with open(DATA_DIR / "armors.json", encoding="utf-8") as f:
            self._armors = json.load(f)["armors"]

    # ── Lookup ───────────────────────────────────────────────────────────────

    def get_weapon(self, weapon_id: str) -> dict:
        """Return the weapon data dict for the given id.  Raises KeyError if missing."""
        for w in self._weapons:
            if w["id"] == weapon_id:
                return w
        raise KeyError(weapon_id)

    def get_armor(self, armor_id: str) -> dict:
        """Return the armor data dict for the given id.  Raises KeyError if missing."""
        for a in self._armors:
            if a["id"] == armor_id:
                return a
        raise KeyError(armor_id)

    def weapons_by_grade(self, grade: str) -> list[dict]:
        """Return all weapons of the given grade."""
        return [w for w in self._weapons if w.get("grade") == grade]

    def armors_by_type(self, armor_type: str) -> list[dict]:
        """Return all armors of the given type."""
        return [a for a in self._armors if a.get("type") == armor_type]

    # ── Grade helpers ────────────────────────────────────────────────────────

    def grade_level(self, grade: str) -> int:
        """Return the 1-based index of grade in GRADES (Iron=1 … Draconic=5)."""
        try:
            return self.GRADES.index(grade) + 1
        except ValueError:
            return 0

    def next_grade(self, grade: str) -> str | None:
        """Return the next upgrade grade, or None if already Draconic."""
        idx = self.GRADES.index(grade) if grade in self.GRADES else -1
        if idx < 0 or idx >= len(self.GRADES) - 1:
            return None
        return self.GRADES[idx + 1]

    def upgrade_cost(self, weapon: dict) -> int | None:
        """Return the gold cost to upgrade weapon to the next grade.

        Returns None if the weapon is already Draconic.
        Cost formula: base_price × 1.5 × current_grade_level.
        """
        grade = weapon.get("grade", "Iron")
        if grade == "Draconic":
            return None
        level = weapon.get("grade_level", self.grade_level(grade))
        return int(weapon.get("price", 0) * 1.5 * level)

    # ── Shop helpers ─────────────────────────────────────────────────────────

    def available_shop_weapons(self, max_grade: str) -> list[dict]:
        """Return all weapons with grade_level <= max_grade level."""
        max_lvl = self.grade_level(max_grade)
        return [w for w in self._weapons if w.get("grade_level", 1) <= max_lvl]

    def available_shop_armors(self) -> list[dict]:
        """Return all armors (all types available in the Store at all times)."""
        return list(self._armors)

    def sell_price(self, item: dict) -> int:
        """Return 50 % of the item's buy price, rounded down."""
        return item.get("price", 0) // 2

    # ── Store stock generation ────────────────────────────────────────────────

    def random_store_items(self, count: int = 3) -> list[dict]:
        """Return `count` unique randomly-selected items (weapons + armors).

        Items are weighted by inverse rarity — Iron appears most often,
        Draconic very rarely.  Each returned dict has an extra '_item_type'
        key set to 'weapon' or 'armor'.
        """
        pool: list[tuple[dict, str]] = []  # (item_dict, "weapon"/"armor")
        weights: list[int]           = []

        for w in self._weapons:
            lvl = w.get("grade_level", 1)
            pool.append((w, "weapon"))
            weights.append(_GRADE_WEIGHTS.get(lvl, 1))

        for a in self._armors:
            lvl = a.get("grade_level", 1)
            pool.append((a, "armor"))
            weights.append(_GRADE_WEIGHTS.get(lvl, 1))

        chosen = random.choices(pool, weights=weights, k=count * 4)
        # Deduplicate (by id) while preserving order
        seen:  set[str]  = set()
        items: list[dict] = []
        for item, itype in chosen:
            iid = item["id"]
            if iid not in seen:
                seen.add(iid)
                tagged = dict(item)
                tagged["_item_type"] = itype
                items.append(tagged)
            if len(items) == count:
                break

        # Pad with deterministic fallback if pool was too small
        while len(items) < count:
            item, itype = pool[len(items) % len(pool)]
            tagged = dict(item)
            tagged["_item_type"] = itype
            items.append(tagged)

        return items

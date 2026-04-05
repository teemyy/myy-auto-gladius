from __future__ import annotations


class Armor:
    """An equippable armor piece loaded from src/data/armors.json.

    Armor modifies a gladiator's HP pool and/or flat damage reduction and may
    carry effect tags (e.g. "thorns", "fire_resist").
    """

    def __init__(
        self,
        id_: str,
        name: str,
        hp_bonus: int,
        defense_bonus: int,
        effects: list[str],
        price: int,
        sprite: str,
    ):
        self.id             = id_
        self.name           = name
        self.hp_bonus       = hp_bonus
        self.defense_bonus  = defense_bonus
        self.effects        = effects   # e.g. ["thorns", "fire_resist"]
        self.price          = price
        self.sprite         = sprite    # path relative to assets/images/items/

    # ------------------------------------------------------------------

    def has_effect(self, effect: str) -> bool:
        """Return True if this armor carries the named effect tag."""
        pass

    def sell_price(self) -> int:
        """Return gold recovered when selling (typically 50% of buy price)."""
        pass

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict for save files."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Armor":
        """Construct an Armor from a raw data dict (armors.json entry)."""
        pass

    def __repr__(self) -> str:
        return f"<Armor {self.name!r} hp+{self.hp_bonus} def+{self.defense_bonus}>"

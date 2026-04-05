from __future__ import annotations


class Weapon:
    """An equippable weapon loaded from src/data/weapons.json.

    Weapons modify a gladiator's attack damage and/or attack range and may
    carry one or more named effect tags that the combat system checks.
    """

    def __init__(
        self,
        id_: str,
        name: str,
        damage_bonus: int,
        range_bonus: float,
        effects: list[str],
        price: int,
        sprite: str,
    ):
        self.id           = id_           # unique key matching weapons.json
        self.name         = name
        self.damage_bonus = damage_bonus
        self.range_bonus  = range_bonus
        self.effects      = effects       # e.g. ["knockback", "bleed"]
        self.price        = price
        self.sprite       = sprite        # path relative to assets/images/items/

    # ------------------------------------------------------------------

    def has_effect(self, effect: str) -> bool:
        """Return True if this weapon carries the named effect tag."""
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
    def from_dict(cls, data: dict) -> "Weapon":
        """Construct a Weapon from a raw data dict (weapons.json entry)."""
        pass

    def __repr__(self) -> str:
        return f"<Weapon {self.name!r} dmg+{self.damage_bonus} rng+{self.range_bonus}>"

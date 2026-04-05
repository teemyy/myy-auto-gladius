from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .weapon import Weapon
    from .armor import Armor
    from .passive import Passive


class GladiatorStatus:
    HEALTHY  = "healthy"
    INJURED  = "injured"   # misses next fight
    RETIRED  = "retired"   # age >= MAX_SEASONS
    DEAD     = "dead"      # killed in battle


MAX_SEASONS = 15  # gladiators retire after this many seasons


class Gladiator:
    """A single gladiator on a team roster.

    Holds base stats, equipped items, passive ability, and lifecycle state.
    Does *not* subclass pygame.sprite — the combat system creates a separate
    sprite when the gladiator enters the arena.
    """

    def __init__(
        self,
        name: str,
        portrait: str,
        hp: int,
        speed: float,
        attack: int,
        range_: float,
        defense: int,
        passive: "Passive",
    ):
        self.name     = name
        self.portrait = portrait  # path relative to assets/images/portraits/

        # Base stats (before equipment)
        self.base_hp      = hp
        self.base_speed   = speed
        self.base_attack  = attack
        self.base_range   = range_
        self.base_defense = defense

        self.passive: "Passive"       = passive
        self.weapon:  "Weapon | None" = None
        self.armor:   "Armor  | None" = None

        self.seasons_active: int = 0
        self.status: str         = GladiatorStatus.HEALTHY

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def effective_stats(self) -> dict:
        """Return final stats after applying weapon and armor bonuses."""
        pass

    # ------------------------------------------------------------------
    # Equipment
    # ------------------------------------------------------------------

    def equip_weapon(self, weapon: "Weapon") -> "Weapon | None":
        """Equip a weapon; return the previously equipped weapon (or None)."""
        pass

    def unequip_weapon(self) -> "Weapon | None":
        """Remove and return the equipped weapon."""
        pass

    def equip_armor(self, armor: "Armor") -> "Armor | None":
        """Equip armor; return the previously equipped armor (or None)."""
        pass

    def unequip_armor(self) -> "Armor | None":
        """Remove and return the equipped armor."""
        pass

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the gladiator can fight (healthy and alive)."""
        pass

    def apply_battle_outcome(self, survived: bool, injury_roll: float) -> None:
        """Called after a fight to apply death, injury, or healthy outcome.

        Args:
            survived:     False if the gladiator was killed during the fight.
            injury_roll:  Random float 0–1; compared against injury threshold.
        """
        pass

    def recover_from_injury(self) -> None:
        """Clear an injury status at the start of a new fight (one fight missed)."""
        pass

    def advance_season(self) -> None:
        """Increment season counter; trigger retirement if MAX_SEASONS reached."""
        pass

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict for save files."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Gladiator":
        """Reconstruct a Gladiator from a saved dict."""
        pass

    def __repr__(self) -> str:
        return f"<Gladiator {self.name!r} status={self.status}>"

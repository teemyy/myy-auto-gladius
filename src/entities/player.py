from __future__ import annotations
from .entity import BaseEntity
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..systems.limb_system import LimbSystem


class Player(BaseEntity):
    """The player character.

    Extends BaseEntity with gold, STR, AGI, a LimbSystem, and
    one weapon + one armor equipment slot.

    Stats:
        strength   -- increases attack damage dealt; increases physical damage reduction
        agility    -- increases crit chance %; increases evasion chance %
        endurance  -- governs max stamina pool; training END raises max_stamina

    All default stat values are loaded from settings.py — never hardcoded here.
    """

    def __init__(
        self,
        name:      str,
        hp:        int,
        stamina:   int,
        gold:      int,
        strength:  int,
        agility:   int,
        endurance: int,
    ):
        super().__init__(name, hp, stamina)
        self.gold:      int   = gold
        self.strength:  int   = strength   # damage bonus + physical damage reduction
        self.agility:   int   = agility    # crit chance % + evasion chance %
        self.endurance: int   = endurance  # governs max stamina pool

        self.weapon:   dict | None = None   # loaded weapon data dict
        self.armor:    dict | None = None   # loaded armor data dict
        self.limbs:    "LimbSystem | None" = None   # injected after construction

        self.stage:    int  = 1
        self.victories: int = 0

    # ── Equipment ────────────────────────────────────────────────────────────

    def equip_weapon(self, weapon: dict) -> dict | None:
        """Equip a weapon dict; return the previously equipped weapon or None."""
        pass

    def unequip_weapon(self) -> dict | None:
        """Remove and return the equipped weapon."""
        pass

    def equip_armor(self, armor: dict) -> dict | None:
        """Equip an armor dict; return the previously equipped armor or None."""
        pass

    def unequip_armor(self) -> dict | None:
        """Remove and return the equipped armor."""
        pass

    def has_ranged_weapon(self) -> bool:
        """Return True if the equipped weapon supports the Ranged action."""
        pass

    # ── Actions ──────────────────────────────────────────────────────────────

    def available_actions(self) -> list[str]:
        """Return the list of actions the player can legally choose this round.

        Filters out:
        - Ranged if no ranged weapon is equipped
        - Quick if L-Arm is destroyed (limb wound effect)
        - All offensive actions if R-Arm is destroyed (forced Defend)
        - All actions except Defend if stamina is zero
        """
        pass

    def choose_action(self, action: str) -> bool:
        """Validate and commit the player's chosen action for this round.

        Returns False if the action is not in available_actions().
        """
        pass

    # ── Economy ──────────────────────────────────────────────────────────────

    def earn_gold(self, amount: int) -> None:
        """Add gold to the player's balance."""
        pass

    def spend_gold(self, amount: int) -> bool:
        """Deduct gold. Returns False without modifying balance if insufficient."""
        pass

    # ── Progression ──────────────────────────────────────────────────────────

    def advance_stage(self) -> None:
        """Increment stage counter and record the victory."""
        pass

    def train_strength(self) -> None:
        """Increase strength by 1 point (called by Training Ground)."""
        pass

    def train_agility(self) -> None:
        """Increase agility by 1 point (called by Training Ground)."""
        pass

    def train_endurance(self, stamina_per_end: int = 5) -> None:
        """Increase endurance by 1 point and raise max_stamina by stamina_per_end."""
        pass

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise full player state for save files."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """Reconstruct a Player from a saved dict."""
        pass

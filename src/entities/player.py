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
        old = self.weapon
        self.weapon = weapon
        return old

    def unequip_weapon(self) -> dict | None:
        """Remove and return the equipped weapon."""
        old = self.weapon
        self.weapon = None
        return old

    def equip_armor(self, armor: dict) -> dict | None:
        """Equip an armor dict; return the previously equipped armor or None."""
        old = self.armor
        self.armor = armor
        return old

    def unequip_armor(self) -> dict | None:
        """Remove and return the equipped armor."""
        old = self.armor
        self.armor = None
        return old

    def has_ranged_weapon(self) -> bool:
        """Return True if the equipped weapon supports the Ranged action."""
        if not self.weapon:
            return False
        return "Ranged" in self.weapon.get("available_actions", [])

    # ── Actions ──────────────────────────────────────────────────────────────

    def available_actions(self) -> list[str]:
        """Return the list of actions the player can legally choose this round.

        Filters out:
        - Ranged if no ranged weapon is equipped
        - Quick if L-Arm is destroyed (limb wound effect)
        - All offensive actions if R-Arm is destroyed (forced Defend)
        - All actions except Defend if stamina is zero
        """
        if self.weapon:
            actions = list(self.weapon.get("available_actions", ["Heavy", "Quick"]))
        else:
            actions = ["Heavy", "Quick"]

        if "Defend" not in actions:
            actions.append("Defend")

        if not self.has_ranged_weapon():
            actions = [a for a in actions if a != "Ranged"]

        if self.limbs:
            penalties = self.limbs.get_combat_penalties()
            if penalties.get("no_quick"):
                actions = [a for a in actions if a != "Quick"]
            if penalties.get("no_defend"):
                actions = [a for a in actions if a != "Defend"]
            if penalties.get("disarmed"):
                # R-Arm destroyed: can only Defend
                actions = [a for a in actions if a == "Defend"]

        if self.stamina <= 0:
            return ["Defend"]

        return actions if actions else ["Defend"]

    def choose_action(self, action: str) -> bool:
        """Validate and commit the player's chosen action for this round.

        Returns False if the action is not in available_actions().
        """
        return action in self.available_actions()

    # ── Economy ──────────────────────────────────────────────────────────────

    def earn_gold(self, amount: int) -> None:
        """Add gold to the player's balance."""
        self.gold += amount

    def spend_gold(self, amount: int) -> bool:
        """Deduct gold. Returns False without modifying balance if insufficient."""
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    # ── Progression ──────────────────────────────────────────────────────────

    def advance_stage(self) -> None:
        """Increment stage counter and record the victory."""
        self.stage += 1
        self.victories += 1

    def train_strength(self) -> None:
        """Increase strength by 1 point (called by Training Ground)."""
        self.strength += 1

    def train_agility(self) -> None:
        """Increase agility by 1 point (called by Training Ground)."""
        self.agility += 1

    def train_endurance(self, stamina_per_end: int = 5) -> None:
        """Increase endurance by 1 point and raise max_stamina by stamina_per_end."""
        self.endurance += 1
        self.max_stamina += stamina_per_end

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise full player state for save files."""
        base = super().to_dict()
        base.update({
            "gold":       self.gold,
            "strength":   self.strength,
            "agility":    self.agility,
            "endurance":  self.endurance,
            "stage":      self.stage,
            "victories":  self.victories,
            "weapon":     self.weapon,
            "armor":      self.armor,
            "limbs":      self.limbs.to_dict() if self.limbs else None,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """Reconstruct a Player from a saved dict."""
        from ..systems.limb_system import LimbSystem
        p = cls(
            name      = data["name"],
            hp        = data["max_hp"],
            stamina   = data["max_stamina"],
            gold      = data["gold"],
            strength  = data["strength"],
            agility   = data["agility"],
            endurance = data["endurance"],
        )
        p.hp        = data["hp"]
        p.stamina   = data["stamina"]
        p.stage     = data.get("stage", 1)
        p.victories = data.get("victories", 0)
        p.weapon    = data.get("weapon")
        p.armor     = data.get("armor")
        if data.get("limbs"):
            p.limbs = LimbSystem.from_dict(data["limbs"])
        return p

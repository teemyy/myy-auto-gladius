from __future__ import annotations

MAX_INTEGRITY = 100

# Wound effects applied when a limb reaches 0 integrity
WOUND_EFFECTS: dict[str, str] = {
    "Head":  "stunned",         # skip next action
    "Torso": "hp_reduced",      # max HP -25 %
    "L-Arm": "no_quick",        # cannot use Quick action
    "R-Arm": "disarmed",        # all attacks -50 % damage
    "L-Leg": "agility_reduced", # agility -30 %
    "R-Leg": "no_defend",       # cannot use Defend action
}


class LimbSystem:
    """Tracks the integrity of each of a combatant's six limbs.

    Integrity runs from 0 (destroyed / wounded) to MAX_INTEGRITY (100, full health).
    When a limb reaches 0, its wound effect is applied to the owning entity for
    the remainder of the fight.  Limbs are restored at the town Healer.
    """

    LIMBS = ("Head", "Torso", "L-Arm", "R-Arm", "L-Leg", "R-Leg")

    def __init__(self):
        self.integrity: dict[str, int] = {}
        self.active_wounds: list[str]  = []   # wound effect strings currently active

    # ── Setup ────────────────────────────────────────────────────────────────

    def initialise(self, starting_integrity: int = 100) -> None:
        """Set all limbs to starting_integrity and clear active wounds."""
        self.integrity = {limb: starting_integrity for limb in self.LIMBS}
        self.active_wounds = []

    # ── Damage ───────────────────────────────────────────────────────────────

    def apply_damage(self, limb: str, amount: int) -> bool:
        """Reduce the limb's integrity by amount (clamped to 0).

        Returns True if the limb just crossed the 0 threshold (newly wounded).
        Automatically adds the limb's wound effect to active_wounds on crossing.
        """
        before = self.integrity.get(limb, 0)
        after  = max(0, before - amount)
        self.integrity[limb] = after
        if before > 0 and after == 0:
            effect = WOUND_EFFECTS.get(limb)
            if effect and effect not in self.active_wounds:
                self.active_wounds.append(effect)
            return True
        return False

    def distribute_damage(self, total_damage: int, weights: dict[str, float] | None = None) -> dict[str, int]:
        """Spread damage across limbs according to weights.

        Default weights match a rough hit-location probability table:
          Torso 40 %, Arms 15 % each, Legs 12 % each, Head 6 %.
        Returns a dict of {limb: damage_applied}.
        """
        if weights is None:
            weights = {
                "Torso": 0.40,
                "L-Arm": 0.15,
                "R-Arm": 0.15,
                "L-Leg": 0.12,
                "R-Leg": 0.12,
                "Head":  0.06,
            }
        result: dict[str, int] = {}
        for limb, w in weights.items():
            dmg = int(total_damage * w)
            if dmg > 0:
                self.apply_damage(limb, dmg)
                result[limb] = dmg
        return result

    # ── State queries ────────────────────────────────────────────────────────

    def get_integrity(self, limb: str) -> int:
        """Return the current integrity of the given limb (0–100)."""
        return self.integrity.get(limb, 0)

    def is_destroyed(self, limb: str) -> bool:
        """Return True if the limb's integrity is 0."""
        return self.integrity.get(limb, 0) == 0

    def has_wound(self, effect: str) -> bool:
        """Return True if the given wound effect is currently active."""
        return effect in self.active_wounds

    def get_combat_penalties(self) -> dict[str, bool | float]:
        """Return a dict of all active penalty flags derived from wounds.

        Keys: "stunned", "hp_reduced", "no_quick", "disarmed",
              "agility_reduced", "no_defend".
        Values are bool or float multipliers depending on the effect.
        """
        return {
            "stunned":         "stunned"         in self.active_wounds,
            "hp_reduced":      "hp_reduced"      in self.active_wounds,
            "no_quick":        "no_quick"        in self.active_wounds,
            "disarmed":        "disarmed"        in self.active_wounds,
            "agility_reduced": "agility_reduced" in self.active_wounds,
            "no_defend":       "no_defend"       in self.active_wounds,
        }

    def all_intact(self) -> bool:
        """Return True when every limb is at full integrity."""
        return all(v >= MAX_INTEGRITY for v in self.integrity.values())

    # ── Restoration ──────────────────────────────────────────────────────────

    def restore_limb(self, limb: str, amount: int) -> int:
        """Increase the limb's integrity by amount (clamped to MAX_INTEGRITY).

        Removes the limb's wound effect from active_wounds if integrity > 0.
        Returns the actual amount restored.
        """
        before = self.integrity.get(limb, 0)
        after  = min(before + amount, MAX_INTEGRITY)
        self.integrity[limb] = after
        actual = after - before
        if after > 0:
            effect = WOUND_EFFECTS.get(limb)
            if effect and effect in self.active_wounds:
                self.active_wounds.remove(effect)
        return actual

    def restore_all(self) -> None:
        """Fully restore every limb to MAX_INTEGRITY (used in tests / Healer full heal)."""
        for limb in self.LIMBS:
            self.integrity[limb] = MAX_INTEGRITY
        self.active_wounds = []

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise integrity and wound state for save files."""
        return {
            "integrity":     dict(self.integrity),
            "active_wounds": list(self.active_wounds),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LimbSystem":
        """Reconstruct a LimbSystem from a saved dict."""
        obj = cls()
        obj.integrity     = dict(data.get("integrity", {}))
        obj.active_wounds = list(data.get("active_wounds", []))
        return obj

from __future__ import annotations


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
        pass

    # ── Damage ───────────────────────────────────────────────────────────────

    def apply_damage(self, limb: str, amount: int) -> bool:
        """Reduce the limb's integrity by amount (clamped to 0).

        Returns True if the limb just crossed the 0 threshold (newly wounded).
        Automatically adds the limb's wound effect to active_wounds on crossing.
        """
        pass

    def distribute_damage(self, total_damage: int, weights: dict[str, float] | None = None) -> dict[str, int]:
        """Spread damage across limbs according to weights.

        Default weights match a rough hit-location probability table:
          Torso 40 %, Arms 15 % each, Legs 12 % each, Head 6 %.
        Returns a dict of {limb: damage_applied}.
        """
        pass

    # ── State queries ────────────────────────────────────────────────────────

    def get_integrity(self, limb: str) -> int:
        """Return the current integrity of the given limb (0–100)."""
        pass

    def is_destroyed(self, limb: str) -> bool:
        """Return True if the limb's integrity is 0."""
        pass

    def has_wound(self, effect: str) -> bool:
        """Return True if the given wound effect is currently active."""
        pass

    def get_combat_penalties(self) -> dict[str, bool | float]:
        """Return a dict of all active penalty flags derived from wounds.

        Keys: "stunned", "hp_reduced", "no_quick", "disarmed",
              "agility_reduced", "no_defend".
        Values are bool or float multipliers depending on the effect.
        """
        pass

    def all_intact(self) -> bool:
        """Return True when every limb is at full integrity."""
        pass

    # ── Restoration ──────────────────────────────────────────────────────────

    def restore_limb(self, limb: str, amount: int) -> int:
        """Increase the limb's integrity by amount (clamped to MAX_INTEGRITY).

        Removes the limb's wound effect from active_wounds if integrity > 0.
        Returns the actual amount restored.
        """
        pass

    def restore_all(self) -> None:
        """Fully restore every limb to MAX_INTEGRITY (used in tests / Healer full heal)."""
        pass

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialise integrity and wound state for save files."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "LimbSystem":
        """Reconstruct a LimbSystem from a saved dict."""
        pass

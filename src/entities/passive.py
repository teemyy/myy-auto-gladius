from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gladiator import Gladiator


class TriggerEvent:
    """Named trigger points the combat system fires passive checks against."""
    ON_ATTACK       = "on_attack"        # gladiator lands a hit
    ON_HIT_TAKEN    = "on_hit_taken"     # gladiator receives damage
    ON_KILL         = "on_kill"          # gladiator kills an opponent
    ON_BATTLE_START = "on_battle_start"  # once at the start of each fight
    ON_MOVE         = "on_move"          # each movement tick


class Passive:
    """A single passive ability attached to a gladiator.

    Loaded from src/data/passives.json. The combat system calls
    ``should_trigger()`` at the relevant event, then ``apply()`` if it fires.

    Params keys and meaning vary by passive id — see passives.json for the
    canonical schema per ability.
    """

    def __init__(
        self,
        id_: str,
        name: str,
        description: str,
        trigger: str,
        params: dict,
    ):
        self.id          = id_          # unique key matching passives.json
        self.name        = name
        self.description = description
        self.trigger     = trigger      # one of the TriggerEvent constants
        self.params      = params       # e.g. {"chance": 0.2, "multiplier": 2.0}

    # ------------------------------------------------------------------

    def should_trigger(self, event: str, context: dict) -> bool:
        """Return True if this passive should fire for the given event + context.

        Args:
            event:   One of the TriggerEvent constants.
            context: Dict with keys like ``attacker``, ``defender``,
                     ``damage``, ``roll`` provided by the combat system.
        """
        pass

    def apply(self, owner: "Gladiator", context: dict) -> dict:
        """Execute the passive effect and return a modified context dict.

        The returned dict may contain keys such as:
          - ``damage``        modified damage value
          - ``stun_duration`` seconds the target is stunned
          - ``heal``          HP to restore to the owner
          - ``extra_projectiles`` count of bonus projectiles to spawn
        """
        pass

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> "Passive":
        """Construct a Passive from a raw data dict (passives.json entry)."""
        pass

    def __repr__(self) -> str:
        return f"<Passive {self.name!r} trigger={self.trigger}>"

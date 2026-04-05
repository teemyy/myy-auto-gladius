from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.gladiator import Gladiator
    from ..entities.team import Team


@dataclass
class CombatantState:
    """Runtime combat state for one gladiator — separate from the roster Gladiator.

    The CombatSystem creates one of these per fighter at battle start and reads
    the gladiator's effective_stats() to populate it.
    """
    gladiator:       "Gladiator"
    current_hp:      int
    is_alive:        bool    = True
    is_stunned:      bool    = False
    stun_remaining:  float   = 0.0   # seconds
    cooldown:        float   = 0.0   # seconds until next attack


@dataclass
class BattleResult:
    """Summary returned by CombatSystem.resolve_battle()."""
    winner_team:   "Team"
    loser_team:    "Team"
    survivors_a:   list["Gladiator"] = field(default_factory=list)
    survivors_b:   list["Gladiator"] = field(default_factory=list)
    killed:        list["Gladiator"] = field(default_factory=list)
    injured:       list["Gladiator"] = field(default_factory=list)
    round_count:   int               = 0


class CombatSystem:
    """Resolves auto-battles between two teams.

    ``resolve_battle`` is the main entry point.  It drives the step-by-step
    simulation and returns a ``BattleResult`` when one side is eliminated.

    The system also exposes lower-level helpers used by the arena screen to
    animate the fight frame-by-frame (``step``), and by the passive system to
    fire ability callbacks at the correct moments.
    """

    MAX_ROUNDS = 500  # safety cap to prevent infinite loops

    def __init__(self):
        self.states_a: list[CombatantState] = []
        self.states_b: list[CombatantState] = []
        self._round:   int                  = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve_battle(self, team_a: "Team", team_b: "Team") -> BattleResult:
        """Simulate the full battle between two teams and return the result.

        Calls ``setup``, then steps the simulation until one side is wiped out
        or ``MAX_ROUNDS`` is reached.
        """
        pass

    def setup(self, team_a: "Team", team_b: "Team") -> None:
        """Initialise CombatantStates for both teams at the start of a battle."""
        pass

    def step(self, dt: float) -> bool:
        """Advance the simulation by ``dt`` seconds.

        Returns True when the battle is over (one side eliminated).
        Called each frame by the arena screen for animated playback.
        """
        pass

    def is_over(self) -> bool:
        """Return True if one side has no living combatants."""
        pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pick_target(self, attacker: CombatantState, enemies: list[CombatantState]) -> CombatantState | None:
        """Return the nearest living enemy to the attacker, or None."""
        pass

    def _move_toward(self, attacker: CombatantState, target: CombatantState, dt: float) -> None:
        """Advance attacker toward target by speed * dt."""
        pass

    def _resolve_attack(self, attacker: CombatantState, defender: CombatantState) -> int:
        """Calculate and apply damage from one attack.

        Applies defense reduction, triggers the attacker's passive if applicable,
        and returns the final damage dealt.
        """
        pass

    def _trigger_passive(self, owner: CombatantState, event: str, context: dict) -> dict:
        """Check and apply the owner's passive for the given trigger event.

        Returns the (possibly modified) context dict.
        """
        pass

    def _build_result(self) -> BattleResult:
        """Construct the BattleResult from the final simulation state."""
        pass

    def _apply_post_battle_outcomes(self, result: BattleResult) -> None:
        """Roll for injuries on survivors; mark killed gladiators as dead."""
        pass

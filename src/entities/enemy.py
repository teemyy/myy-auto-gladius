from __future__ import annotations
from .entity import BaseEntity
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..systems.limb_system import LimbSystem


class AIDifficulty:
    """Named difficulty levels that control how the enemy picks actions."""
    EASY   = "easy"    # random action
    NORMAL = "normal"  # simple counter-weighting
    HARD   = "hard"    # reads player tendencies; used by bosses


class Enemy(BaseEntity):
    """An enemy gladiator encountered in a specific stage.

    Loaded from enemies.json.  The AI selects actions via choose_action(),
    whose behaviour changes with ai_difficulty.
    """

    def __init__(
        self,
        name:          str,
        stage:         int,
        hp:            int,
        stamina:       int,
        agility:       int,
        weapon:        dict,
        armor:         dict,
        ai_difficulty: str,
        is_boss:       bool,
        gold_reward:   int,
        description:   str,
    ):
        super().__init__(name, hp, stamina)
        self.stage:         int   = stage
        self.agility:       int   = agility
        self.weapon:        dict  = weapon
        self.armor:         dict  = armor
        self.ai_difficulty: str   = ai_difficulty
        self.is_boss:       bool  = is_boss
        self.gold_reward:   int   = gold_reward
        self.description:   str   = description

        self.limbs: "LimbSystem | None" = None   # injected before battle

        # Internal state for HARD AI
        self._player_action_history: list[str] = []

    # ── AI ───────────────────────────────────────────────────────────────────

    def choose_action(self, player_last_action: str | None = None) -> str:
        """Return the action this enemy will take this round.

        Dispatches to the appropriate AI routine based on ai_difficulty:
        - EASY:   uniform random over available actions
        - NORMAL: weighted random that slightly favours countering last action
        - HARD:   frequency analysis of player_action_history to pick best counter
        """
        pass

    def available_actions(self) -> list[str]:
        """Return legal actions given current stamina and limb state."""
        pass

    def record_player_action(self, action: str) -> None:
        """Append the player's action to history (used by HARD AI)."""
        pass

    # ── Reward ───────────────────────────────────────────────────────────────

    def get_reward(self) -> dict:
        """Return the gold and optional item drop awarded on defeat.

        Return format: {"gold": int, "item": dict | None}
        """
        pass

    # ── Serialisation ────────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Enemy":
        """Construct an Enemy from an enemies.json entry."""
        pass

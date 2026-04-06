from __future__ import annotations
import json
import os
import random
from collections import Counter
from .entity import BaseEntity
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..systems.limb_system import LimbSystem


class AIDifficulty:
    """Named difficulty levels that control how the enemy picks actions."""
    EASY   = "easy"    # random action
    NORMAL = "normal"  # simple counter-weighting
    HARD   = "hard"    # reads player tendencies; used by bosses


# RPS counter table: given what the player just did, what beats it?
_COUNTER: dict[str, str] = {
    "Heavy":  "Quick",
    "Quick":  "Defend",
    "Defend": "Heavy",
    "Ranged": "Defend",
}


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
        strength:      int,
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
        self.strength:      int   = strength  # damage bonus + physical damage reduction
        self.agility:       int   = agility   # crit chance % + evasion chance %
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
        actions = self.available_actions()
        if not actions:
            return "Defend"

        if self.ai_difficulty == AIDifficulty.EASY:
            return random.choice(actions)

        elif self.ai_difficulty == AIDifficulty.NORMAL:
            counter = _COUNTER.get(player_last_action or "", None)
            if counter and counter in actions and random.random() < 0.50:
                return counter
            return random.choice(actions)

        else:  # HARD
            if self._player_action_history:
                most_common = Counter(self._player_action_history).most_common(1)[0][0]
                best_counter = _COUNTER.get(most_common)
                if best_counter and best_counter in actions:
                    return best_counter
            return random.choice(actions)

    def available_actions(self) -> list[str]:
        """Return legal actions given current stamina and limb state."""
        actions = list(self.weapon.get("available_actions", ["Heavy", "Quick"]))
        if "Defend" not in actions:
            actions.append("Defend")

        if self.limbs:
            penalties = self.limbs.get_combat_penalties()
            if penalties.get("no_quick"):
                actions = [a for a in actions if a != "Quick"]
            if penalties.get("no_defend"):
                actions = [a for a in actions if a != "Defend"]
            if penalties.get("disarmed"):
                actions = [a for a in actions if a == "Defend"]

        if self.stamina <= 0:
            return ["Defend"]

        return actions if actions else ["Defend"]

    def record_player_action(self, action: str) -> None:
        """Append the player's action to history (used by HARD AI)."""
        self._player_action_history.append(action)

    # ── Reward ───────────────────────────────────────────────────────────────

    def get_reward(self) -> dict:
        """Return the gold and optional item drop awarded on defeat.

        Return format: {"gold": int, "item": dict | None}
        """
        return {"gold": self.gold_reward, "item": None}

    # ── Serialisation ────────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Enemy":
        """Construct an Enemy from an enemies.json entry."""
        base_dir = os.path.join(os.path.dirname(__file__), "..", "data")

        with open(os.path.join(base_dir, "weapons.json"), encoding="utf-8") as f:
            weapons_data = json.load(f)
        with open(os.path.join(base_dir, "armors.json"), encoding="utf-8") as f:
            armors_data = json.load(f)

        weapon = next(w for w in weapons_data["weapons"] if w["id"] == data["weapon_id"])
        armor  = next(a for a in armors_data["armors"]  if a["id"] == data["armor_id"])

        return cls(
            name          = data["name"],
            stage         = data["stage"],
            hp            = data["hp"],
            stamina       = data["stamina"],
            strength      = data["strength"],
            agility       = data["agility"],
            weapon        = weapon,
            armor         = armor,
            ai_difficulty = data["ai_difficulty"],
            is_boss       = data["is_boss"],
            gold_reward   = data["gold_reward"],
            description   = data["description"],
        )

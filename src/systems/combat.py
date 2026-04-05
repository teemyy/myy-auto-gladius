from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..entities.enemy  import Enemy


# ── RPS outcome table ────────────────────────────────────────────────────────
# Value meanings:  "attacker_hits", "defender_hits", "both_hit", "neither"
RPS_TABLE: dict[tuple[str, str], str] = {
    ("Heavy",  "Heavy"):   "both_hit",
    ("Heavy",  "Quick"):   "defender_hits",   # Quick beats Heavy
    ("Heavy",  "Defend"):  "attacker_hits",   # Heavy beats Defend
    ("Heavy",  "Ranged"):  "both_hit",
    ("Quick",  "Heavy"):   "attacker_hits",
    ("Quick",  "Quick"):   "both_hit",
    ("Quick",  "Defend"):  "defender_hits",   # Defend beats Quick
    ("Quick",  "Ranged"):  "both_hit",
    ("Defend", "Heavy"):   "attacker_hits",   # Heavy breaks Defend
    ("Defend", "Quick"):   "defender_hits",
    ("Defend", "Defend"):  "neither",
    ("Defend", "Ranged"):  "defender_hits",   # Defend beats Ranged
    ("Ranged", "Heavy"):   "both_hit",
    ("Ranged", "Quick"):   "both_hit",
    ("Ranged", "Defend"):  "attacker_hits",
    ("Ranged", "Ranged"):  "both_hit",
}

# ── Material vs armor damage-reduction multipliers ───────────────────────────
# [weapon_damage_type][armor_type] -> float multiplier (1.0 = no change)
MATERIAL_ARMOR_TABLE: dict[str, dict[str, float]] = {
    "slashing": {
        "Cloth":     1.00,
        "Leather":   0.70,   # leather resists slashing
        "Scale":     0.85,
        "Chainmail": 0.65,   # chainmail resists slashing
        "Plate":     0.80,
    },
    "piercing": {
        "Cloth":     1.00,
        "Leather":   1.20,   # leather weak to piercing
        "Scale":     0.60,   # scale resists piercing
        "Chainmail": 0.90,
        "Plate":     0.85,
    },
    "crushing": {
        "Cloth":     1.00,
        "Leather":   1.15,
        "Scale":     1.20,   # scale weak to crushing
        "Chainmail": 1.10,   # chainmail weak to crushing
        "Plate":     0.90,
    },
    "ranged": {
        "Cloth":     1.00,
        "Leather":   0.90,
        "Scale":     0.85,
        "Chainmail": 0.75,
        "Plate":     0.65,   # plate resists ranged
    },
}


@dataclass
class RoundResult:
    """The outcome of a single combat round."""
    player_action:      str
    enemy_action:       str
    outcome:            str               # from RPS_TABLE
    player_damage_in:   int = 0           # damage dealt TO the player
    player_damage_out:  int = 0           # damage dealt BY the player
    player_crit:        bool = False
    enemy_crit:         bool = False
    player_limb_hit:    str | None = None
    enemy_limb_hit:     str | None = None
    new_player_wounds:  list[str] = field(default_factory=list)
    new_enemy_wounds:   list[str] = field(default_factory=list)
    log:                list[str] = field(default_factory=list)


class CombatResolver:
    """Resolves a single round of turn-based combat between a Player and an Enemy.

    Usage:
        resolver = CombatResolver()
        result = resolver.resolve_round(player, enemy, player_action, enemy_action)

    All damage numbers come from the loaded weapon/armor data dicts — never
    from hardcoded constants in this file.
    """

    # ── Public API ───────────────────────────────────────────────────────────

    def resolve_round(
        self,
        player:        "Player",
        enemy:         "Enemy",
        player_action: str,
        enemy_action:  str,
    ) -> RoundResult:
        """Resolve one full round and return a detailed RoundResult.

        Steps:
        1. Determine who hits via RPS_TABLE lookup.
        2. For each hit: calculate base damage from weapon data.
        3. Apply material vs armor reduction via MATERIAL_ARMOR_TABLE.
        4. Roll for critical hit using attacker's agility stat.
        5. Select target limb via LimbSystem.distribute_damage().
        6. Apply damage to entity HP and LimbSystem.
        7. Consume stamina for both sides.
        8. Append human-readable lines to result.log.
        """
        pass

    # ── Damage calculation ───────────────────────────────────────────────────

    def calculate_damage(
        self,
        base_damage:  int,
        damage_type:  str,
        armor_type:   str,
        is_crit:      bool = False,
        crit_mult:    float = 1.5,
    ) -> int:
        """Apply armor reduction and optional crit multiplier to base_damage.

        base_damage × MATERIAL_ARMOR_TABLE[damage_type][armor_type] × crit_mult
        Result is always at least 1.
        """
        pass

    def roll_critical(self, agility: int) -> bool:
        """Return True with probability agility / 100."""
        pass

    # ── RPS resolution ───────────────────────────────────────────────────────

    def resolve_rps(self, attacker_action: str, defender_action: str) -> str:
        """Look up and return the outcome string from RPS_TABLE."""
        pass

    # ── Stamina ──────────────────────────────────────────────────────────────

    def consume_stamina(self, entity, action: str) -> None:
        """Deduct the action's stamina cost from the entity (from settings.STAMINA_COST)."""
        pass

    # ── Win condition ────────────────────────────────────────────────────────

    def is_battle_over(self, player: "Player", enemy: "Enemy") -> str | None:
        """Return 'player_win', 'enemy_win', or None if the fight continues."""
        pass

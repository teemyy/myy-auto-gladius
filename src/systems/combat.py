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

        Order of operations for each potential hit:

        1.  RPS lookup  — determine who lands a hit via RPS_TABLE.
        2.  Evasion check (BEFORE damage) — roll_evasion(defender.agility);
            full miss if triggered; skip all remaining steps for that hit.
        3.  Base damage — read weapon data: damage[action].
        4.  STR damage bonus — base × (1 + attacker.strength × STR_DAMAGE_FACTOR).
        5.  Armor DR — apply MATERIAL_ARMOR_TABLE[damage_type][armor_type].
        6.  STR damage reduction — × (1 - defender.strength × STR_REDUCTION_FACTOR).
        7.  Crit check (AFTER hit confirmed) — roll_critical(attacker.agility);
            if True: final damage × 2; also roll for limb injury on defender.
        8.  Apply damage to HP and LimbSystem.
        9.  Stamina delta — apply STAMINA_DELTA[action] to both sides.
        10. Append human-readable lines to result.log.
        """
        pass

    # ── Damage calculation ───────────────────────────────────────────────────

    # STR scaling constants — tune here only, never in calling code
    STR_DAMAGE_FACTOR    = 0.02   # +2 % damage per STR point
    STR_REDUCTION_FACTOR = 0.01   # −1 % incoming damage per STR point (after armor)

    def calculate_damage(
        self,
        base_damage:  int,
        damage_type:  str,
        armor_type:   str,
        attacker_str: int   = 0,
        defender_str: int   = 0,
        is_crit:      bool  = False,
    ) -> int:
        """Apply the full damage pipeline and return final integer damage.

        Formula (applied in order):
            str_boosted  = base_damage × (1 + attacker_str × STR_DAMAGE_FACTOR)
            after_armor  = str_boosted × MATERIAL_ARMOR_TABLE[damage_type][armor_type]
            after_str_dr = after_armor × (1 − defender_str × STR_REDUCTION_FACTOR)
            final        = after_str_dr × 2  (if is_crit, doubles final damage)

        Result is always at least 1.
        Precondition: roll_evasion() has already been checked and returned False.
        """
        pass

    def roll_critical(self, agility: int) -> bool:
        """Return True with probability agility / 100.

        Called AFTER a hit is confirmed (evasion already failed).
        On True: damage is doubled AND a limb injury roll is triggered.
        """
        pass

    def roll_evasion(self, agility: int) -> bool:
        """Return True with probability agility / 100.

        Called BEFORE damage calculation.  On True: the hit is a full miss —
        no damage, no limb roll, no crit possible for this hit.
        Independent roll from roll_critical.
        """
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

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# Unarmed fallback when R-Arm is severed
FIST_WEAPON: dict = {
    "id":                "fist",
    "name":              "Fist",
    "grade":             "None",
    "grade_level":       0,
    "damage_type":       "crushing",
    "damage":            {"Heavy": 4, "Quick": 2},
    "stamina_cost":      {"Heavy": 8, "Quick": 4},
    "crit_multiplier":   1.0,
    "available_actions": ["Heavy", "Quick"],
}

# Chance per crit to trigger a limb injury/sever roll
_LIMB_CRIT_CHANCE = 0.15

if TYPE_CHECKING:
    from ..entities.player import Player
    from ..entities.enemy  import Enemy


# ── RPS outcome table ────────────────────────────────────────────────────────
# Value meanings:  "attacker_hits", "defender_hits", "both_hit", "neither"
RPS_TABLE: dict[tuple[str, str], str] = {
    # Key: (player_action, enemy_action)
    # "attacker_hits" = player wins,  "defender_hits" = enemy wins
    #
    # RPS cycle:  Heavy > Defend > Quick > Heavy   (Ranged loses to Defend)
    ("Heavy",  "Heavy"):   "both_hit",
    ("Heavy",  "Quick"):   "defender_hits",   # Quick beats Heavy   → enemy wins
    ("Heavy",  "Defend"):  "attacker_hits",   # Heavy beats Defend  → player wins
    ("Heavy",  "Ranged"):  "both_hit",
    ("Quick",  "Heavy"):   "attacker_hits",   # Quick beats Heavy   → player wins
    ("Quick",  "Quick"):   "both_hit",
    ("Quick",  "Defend"):  "defender_hits",   # Defend beats Quick  → enemy wins
    ("Quick",  "Ranged"):  "both_hit",
    ("Defend", "Heavy"):   "defender_hits",   # Heavy beats Defend  → enemy wins
    ("Defend", "Quick"):   "attacker_hits",   # Defend beats Quick  → player wins
    ("Defend", "Defend"):  "neither",
    ("Defend", "Ranged"):  "neither",          # Defend blocks Ranged — no counter
    ("Ranged", "Heavy"):   "both_hit",
    ("Ranged", "Quick"):   "both_hit",
    ("Ranged", "Defend"):  "neither",          # Defend blocks Ranged — no counter
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

# Stamina deltas per action (overrides settings.py for combat)
_STAMINA_DELTA: dict[str, int] = {
    "Heavy":  -3,
    "Quick":  -1,
    "Defend": +2,
    "Ranged": -2,
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
    new_player_wounds:    list[str] = field(default_factory=list)  # severed (integrity 0)
    new_enemy_wounds:     list[str] = field(default_factory=list)
    new_player_injuries:  list[str] = field(default_factory=list)  # partial (integrity 50)
    new_enemy_injuries:   list[str] = field(default_factory=list)
    log:                  list[str] = field(default_factory=list)


class CombatResolver:
    """Resolves a single round of turn-based combat between a Player and an Enemy."""

    STR_DAMAGE_FACTOR    = 0.02   # +2 % damage per STR point
    STR_REDUCTION_FACTOR = 0.01   # −1 % incoming damage per STR point (after armor)

    # ── Public API ───────────────────────────────────────────────────────────

    def resolve_round(
        self,
        player:        "Player",
        enemy:         "Enemy",
        player_action: str,
        enemy_action:  str,
    ) -> RoundResult:
        """Resolve one full round and return a detailed RoundResult."""
        result = RoundResult(
            player_action = player_action,
            enemy_action  = enemy_action,
            outcome       = "",
        )

        outcome = self.resolve_rps(player_action, enemy_action)
        result.outcome = outcome

        player_hits = outcome in ("attacker_hits", "both_hit")
        enemy_hits  = outcome in ("defender_hits", "both_hit")

        # ── Player attacks enemy ──────────────────────────────────────────
        if player_hits:
            self._apply_attack(
                attacker        = player,
                defender        = enemy,
                action          = player_action,
                result          = result,
                is_player_attack= True,
            )

        # ── Enemy attacks player ──────────────────────────────────────────
        if enemy_hits:
            self._apply_attack(
                attacker        = enemy,
                defender        = player,
                action          = enemy_action,
                result          = result,
                is_player_attack= False,
            )

        if not player_hits and not enemy_hits:
            result.log.append("Both combatants block — neither lands a hit.")

        # ── Stamina ───────────────────────────────────────────────────────
        self._apply_stamina(player, player_action)
        self._apply_stamina(enemy,  enemy_action)

        return result

    # ── Damage calculation ───────────────────────────────────────────────────

    def calculate_damage(
        self,
        base_damage:  int,
        damage_type:  str,
        armor_type:   str,
        attacker_str: int   = 0,
        defender_str: int   = 0,
        is_crit:      bool  = False,
    ) -> int:
        """Apply the full damage pipeline and return final integer damage."""
        dmg = base_damage * (1.0 + attacker_str * self.STR_DAMAGE_FACTOR)
        armor_mult = MATERIAL_ARMOR_TABLE.get(damage_type, {}).get(armor_type, 1.0)
        dmg *= armor_mult
        dmg *= (1.0 - defender_str * self.STR_REDUCTION_FACTOR)
        if is_crit:
            dmg *= 2.0
        return max(1, int(dmg))

    def roll_critical(self, agility: int) -> bool:
        """Return True with probability agility * 0.8 %."""
        return random.random() < (agility * 0.008)

    def roll_evasion(self, agility: int) -> bool:
        """Return True with probability agility * 0.5 %."""
        return random.random() < (agility * 0.005)

    # ── RPS resolution ───────────────────────────────────────────────────────

    def resolve_rps(self, attacker_action: str, defender_action: str) -> str:
        """Look up and return the outcome string from RPS_TABLE."""
        return RPS_TABLE.get((attacker_action, defender_action), "both_hit")

    # ── Stamina ──────────────────────────────────────────────────────────────

    def consume_stamina(self, entity, action: str) -> None:
        """Deduct the action's stamina cost from the entity."""
        self._apply_stamina(entity, action)

    # ── Win condition ────────────────────────────────────────────────────────

    def is_battle_over(self, player: "Player", enemy: "Enemy") -> str | None:
        """Return 'player_win', 'enemy_win', or None if the fight continues."""
        if not player.is_alive:
            return "enemy_win"
        if not enemy.is_alive:
            return "player_win"
        return None

    # ── Private helpers ──────────────────────────────────────────────────────

    def _apply_attack(self, attacker, defender, action: str, result: RoundResult, is_player_attack: bool) -> None:
        """Resolve one directional attack, updating result in place."""
        # Select weapon based on action type
        if action == "Ranged":
            # Use the ranged slot; fall back to general weapon if no separate slot
            weapon   = getattr(attacker, "ranged_weapon", None) or attacker.weapon
            disarmed = False
        else:
            # Melee: R-Arm severed → fight with fist
            disarmed = attacker.limbs and attacker.limbs.has_wound("disarmed")
            weapon   = FIST_WEAPON if disarmed else (attacker.weapon or None)

        if weapon:
            avail_dmg = weapon.get("damage", {})
            base_dmg  = avail_dmg.get(action)
            if base_dmg is None:
                base_dmg     = min(avail_dmg.values()) if avail_dmg else 3
                action_label = "counter" if not disarmed else "fist"
            else:
                action_label = "fist" if disarmed else action
            dmg_type = (weapon.get("damage_types") or {}).get(action) \
                       or weapon.get("damage_type", "slashing")
        else:
            base_dmg     = 3
            dmg_type     = "crushing"
            action_label = "fist"

        armor_type = defender.armor.get("type", "Cloth") if defender.armor else "Cloth"

        # Effective agility (may be reduced by limb wounds)
        def_agi = defender.agility
        atk_agi = attacker.agility
        if attacker.limbs and attacker.limbs.has_wound("agility_reduced"):
            atk_agi = int(atk_agi * 0.7)
        if defender.limbs and defender.limbs.has_wound("agility_reduced"):
            def_agi = int(def_agi * 0.7)

        # Evasion check
        if self.roll_evasion(def_agi):
            result.log.append(f"{defender.name} evades {attacker.name}'s {action_label}!")
            return

        # Crit check
        is_crit = self.roll_critical(atk_agi)

        dmg    = self.calculate_damage(base_dmg, dmg_type, armor_type,
                                       attacker.strength, defender.strength, is_crit)
        actual = defender.take_damage(dmg)

        if is_player_attack:
            result.player_damage_out = actual
            result.player_crit       = is_crit
        else:
            result.player_damage_in  = actual
            result.enemy_crit        = is_crit

        crit_tag = "CRITICAL! " if is_crit else ""
        result.log.append(
            f"{crit_tag}{attacker.name} hits {defender.name} with {action_label} for {actual}."
        )

        # Limb system: 15 % chance per crit to injure or sever a limb
        if is_crit and defender.limbs and random.random() < _LIMB_CRIT_CHANCE:
            limb = random.choice(list(defender.limbs.LIMBS))
            cur  = defender.limbs.get_integrity(limb)

            if cur > 50:
                # First strike: injure (bring to 50, no wound effect yet)
                defender.limbs.apply_damage(limb, cur - 50)
                result.log.append(f"  {defender.name}'s {limb} is injured!")
                if is_player_attack:
                    result.enemy_limb_hit = limb
                    result.new_enemy_injuries.append(limb)
                else:
                    result.player_limb_hit = limb
                    result.new_player_injuries.append(limb)
            elif cur > 0:
                # Already injured: sever (bring to 0, wound effect triggers)
                newly_severed = defender.limbs.apply_damage(limb, cur)
                result.log.append(f"  {defender.name}'s {limb} is SEVERED!")
                if is_player_attack:
                    result.enemy_limb_hit = limb
                    if newly_severed:
                        result.new_enemy_wounds.append(limb)
                else:
                    result.player_limb_hit = limb
                    if newly_severed:
                        result.new_player_wounds.append(limb)

    def _apply_stamina(self, entity, action: str) -> None:
        delta = _STAMINA_DELTA.get(action, 0)
        if delta < 0:
            entity.stamina = max(0, entity.stamina + delta)
        else:
            entity.stamina = min(entity.max_stamina, entity.stamina + delta)

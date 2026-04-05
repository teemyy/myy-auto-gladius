# myy-auto-gladius

## Game Concept

Turn-based 2D gladiator RPG. The player fights through **12 stages** in an arena,
returning to a **town hub** between fights to heal, upgrade equipment, and train.
Bosses appear at stages 4, 8, and 12 — each equipped with Draconic-grade gear.

The tone is gritty and tactical: combat decisions matter, injuries persist, and
gold is always tight.

---

## Combat System

### Action Types (Rock-Paper-Scissors)

| Action | Beats | Loses to |
|--------|-------|----------|
| **Heavy** | Defend | Quick |
| **Quick** | Heavy | Defend |
| **Defend** | Quick, Ranged | Heavy |
| **Ranged** | — | Defend |

Each round both sides choose an action simultaneously. The outcome determines
who lands a hit, whether a critical fires, and how much stamina is consumed.

When neither action beats the other (e.g. Heavy vs Heavy) both sides trade hits.

### Actions in detail

- **Heavy** — slow, powerful strike; overwhelms a guard but telegraphed
- **Quick** — fast strike; dodges under a heavy swing but can be deflected
- **Defend** — guard stance; absorbs Quick and Ranged; broken by Heavy
- **Ranged** — projectile attack; only available with ranged weapons; countered by Defend

---

## Player Stats

| Stat | Description |
|------|-------------|
| HP | Hit points; reaching 0 = death |
| Stamina | Spent each action; recovers between rounds; 0 stamina forces Defend |
| Gold | Currency for the town hub |
| Agility | Crit chance % (default 10 %; trainable) |

---

## Limb System

Every combatant has **6 limbs**, each with its own integrity (0–100):

| Limb | At 0 integrity — wound effect |
|------|-------------------------------|
| Head | Stunned (skip action) |
| Torso | –25 % max HP |
| L-Arm | –1 available action (cannot Quick) |
| R-Arm | Disarmed (all attacks –50 % damage) |
| L-Leg | –30 % agility |
| R-Leg | Cannot Defend |

Limbs can be restored at the town Healer.  Targeted limb hits are possible
with certain weapons/passives (not in v1).

---

## Equipment

### Weapon Grades (ascending power)

| Grade | Tier | Notes |
|-------|------|-------|
| Iron | 1 | Starter gear |
| Steel | 2 | Common upgrade |
| Mithril | 3 | Light, fast |
| Adamantite | 4 | Heavy, high damage |
| Draconic | 5 | Boss-exclusive or late-game reward |

### Weapon Types

| Type | Damage type | Available actions |
|------|-------------|-------------------|
| Sword | Slashing | Heavy, Quick |
| Spear | Piercing | Heavy, Quick |
| Axe | Slashing | Heavy |
| Mace | Crushing | Heavy |
| Bow | Ranged | Ranged |

### Armor Types + Strengths/Weaknesses

| Armor | vs Slashing | vs Piercing | vs Crushing | vs Ranged | Notes |
|-------|-------------|-------------|-------------|-----------|-------|
| Cloth | Weak | Weak | Weak | Weak | Cheapest; no penalties |
| Leather | Resistant | Weak | Weak | Moderate | Good early option |
| Scale | Moderate | Resistant | Weak | Moderate | Spear-counter |
| Chainmail | Resistant | Moderate | Weak | Resistant | Versatile |
| Plate | Moderate | Moderate | Moderate | Resistant | Best overall; –5 % agility |

Damage reduction is a float multiplier applied after base damage is calculated.
The lookup table lives in `CombatResolver.MATERIAL_ARMOR_TABLE`.

---

## Town Hub

Accessible between every stage.

| Location | Function |
|----------|----------|
| **Smithy** | Buy and sell weapons; upgrade grade |
| **Store** | Buy and sell armor |
| **Training Ground** | Spend gold to increase Agility (+1 % per session) |
| **Healer** | Restore limb integrity; costs gold per limb |

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+ |
| Rendering / input | pygame-ce 2.4+ |
| Game data | JSON files in `src/data/` |
| Tests | pytest |

Resolution: **1280×720** — fixed, no resize.

---

## Folder Structure

```
myy-auto-gladius/
├── main.py                      # Entry point — pygame window + game loop
├── requirements.txt             # pygame-ce, pytest
├── setup.bat                    # Windows venv bootstrap
├── CLAUDE.md
├── .gitignore
├── assets/
│   ├── images/
│   └── sounds/
├── src/
│   ├── settings.py              # Constants: resolution, colors, stat defaults
│   ├── entities/
│   │   ├── entity.py            # BaseEntity — shared HP/stamina logic
│   │   ├── player.py            # Player(BaseEntity) — stats, limbs, equipment
│   │   └── enemy.py             # Enemy(BaseEntity) — grade, AI action selection
│   ├── systems/
│   │   ├── combat.py            # CombatResolver — RPS resolution, damage calc
│   │   ├── limb_system.py       # LimbSystem — per-limb integrity + wound effects
│   │   └── equipment.py         # EquipmentSystem — load items, damage reduction
│   ├── screens/
│   │   ├── arena.py             # ArenaScreen — turn-based fight view
│   │   └── town.py              # TownScreen — hub with Smithy/Store/Training/Healer
│   └── data/
│       ├── weapons.json         # All weapons (5 grades × 5 types)
│       ├── armors.json          # All armor types with reduction tables
│       └── enemies.json         # 12 enemies; bosses at stages 4, 8, 12
└── tests/
```

### Where things live

- **All numbers** — `src/data/*.json`. Python never hardcodes stat values.
- **Entity state** — `src/entities/`. Hold data; no system logic.
- **Logic** — `src/systems/`. Operate on entities; not subclassed from them.
- **Screens** — `src/screens/`. One file per screen; expose `update(dt)`, `draw(surface)`, `handle_event(event)`.
- **Constants** — `src/settings.py` only.

---

## Coding Conventions

- No stat numbers in Python source — all from JSON
- Type hints on all signatures
- `UPPER_SNAKE_CASE` constants, `PascalCase` classes, `snake_case` everything else
- Screen files ≤ 200 lines; extract helpers when they grow beyond that
- Comments only where logic is non-obvious

---

## Development Status

| Feature | Status |
|---------|--------|
| 1280×720 window, 60 FPS loop, ESC quit | Done |
| `BaseEntity`, `Player`, `Enemy` stubs | Done |
| `LimbSystem`, `CombatResolver`, `EquipmentSystem` stubs | Done |
| `ArenaScreen`, `TownScreen` stubs | Done |
| `weapons.json`, `armors.json`, `enemies.json` | Done |
| RPS combat resolution logic | Not started |
| Limb damage application | Not started |
| Equipment damage reduction calculation | Not started |
| Arena screen turn loop | Not started |
| Town hub UI | Not started |
| Save / load | Not started |

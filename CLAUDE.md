# myy-auto-gladius

## Game Concept

Top-down 2D **auto-battler** featuring anime girl gladiators. The player manages a team of 1–4 gladiators competing in a structured league across multiple seasons. Combat is fully automatic — the player's decisions happen *between* fights: recruiting, equipping, and managing the team budget.

The core loop per season:
1. **Between fights** — recruit gladiators, buy/sell equipment, review opponent rosters
2. **Fight** — teams auto-battle in the arena; watch and react
3. **After tournament** — collect prize gold, tend to injured/dead gladiators, prepare for next season

---

## Tournament System

- **2 tournaments per season** (year)
- **Round-robin format** — every team fights every other team exactly once per tournament
- **12 teams total** — 1 player team + 11 AI-controlled teams
- **Standings** — ranked by win rate; tiebreaker is total gold earned
- **Trophy** awarded to the tournament winner each season
- AI teams recruit and equip between tournaments just like the player

---

## Gladiator System

### Stats
Each gladiator has five base stats:

| Stat | Effect |
|------|--------|
| `hp` | Total hit points |
| `speed` | Movement speed (px/s) |
| `attack` | Damage per hit |
| `range` | Attack reach (px) |
| `defense` | Flat damage reduction per hit |

### Equipment
- **1 weapon slot** — modifies `attack`, `range`, and/or adds effects
- **1 armor slot** — modifies `hp`, `defense`, and/or adds effects
- All item stats defined in JSON (`src/data/weapons.json`, `src/data/armors.json`)

### Passives / Powers
Every gladiator has exactly **one passive ability**. Examples:

| Passive | Effect |
|---------|--------|
| Extended Reach | +25% attack range |
| Critical Strike | 20% chance to deal 2× damage |
| Stun Blow | Melee hits have a chance to stun target briefly |
| Multishot | Ranged attacks fire an additional projectile |
| Evasion | Chance to dodge incoming attacks entirely |
| Lifesteal | Heals for a % of damage dealt |
| AOE Strike | Attacks hit all enemies within a small radius |
| Shield Bash | First hit each fight staggers the target |

Passives are defined in `src/data/passives.json`.

### Lifecycle
- **Death** — gladiator is permanently removed from the roster
- **Injury** — gladiator misses the next fight (random recovery)
- **Retirement** — after 15 seasons, gladiator retires regardless of condition

---

## Economy

- **Income** — gold earned from tournament results (more for wins, placement bonuses)
- **Expenses** — weapons, armor, recruiting new gladiators
- Gold is persistent across tournaments within a save
- Budget management between tournaments is a primary gameplay loop

---

## AI Teams

- 11 AI-controlled teams, each with a name, roster, and equipment
- AI teams spend gold to recruit and equip between tournaments
- AI behavior is scripted (not ML): prioritize filling empty slots, upgrade weakest gear first
- Team names and initial rosters generated from `src/data/names.json`

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+ |
| Rendering / input / audio | [pygame-ce](https://pyga.me/) 2.4+ |
| Game data | JSON files under `src/data/` |
| Packaging | `venv` + `requirements.txt` |

- No external game frameworks, no ECS library
- Resolution: **800×600** (default) — switchable to 1280×720 via `settings.py`
- All stats and content in JSON; no hardcoded numbers in Python source

---

## Folder Structure

```
myy-auto-gladius/
├── main.py                        # Entry point
├── requirements.txt               # pygame-ce
├── setup.bat                      # Windows venv bootstrap
├── assets/
│   ├── images/                    # Sprites, portraits, UI elements
│   └── sounds/                    # SFX, music
├── src/
│   ├── settings.py                # Resolution, FPS, colors, layout constants
│   ├── game.py                    # Main loop, clock, screen/scene dispatch
│   ├── data/                      # Static game data (JSON)
│   │   ├── weapons.json
│   │   ├── armors.json
│   │   ├── passives.json
│   │   └── names.json             # Gladiator and team name pools
│   ├── entities/
│   │   ├── entity.py              # Base combatant (move, target, attack, HP bar)
│   │   ├── gladiator.py           # Gladiator: stats, equipment, passive, lifecycle
│   │   ├── team.py                # Team: roster, gold, record
│   │   └── projectile.py         # Projectile entity for ranged attacks
│   ├── systems/
│   │   ├── combat.py              # Auto-battle resolution, passive triggers
│   │   ├── tournament.py          # Round-robin scheduling, standings, trophies
│   │   ├── economy.py             # Gold income, shop transactions
│   │   └── ai.py                  # AI team decision-making between tournaments
│   └── screens/
│       ├── arena.py               # Live battle view
│       ├── management.py          # Between-tournament roster/equipment screen
│       └── bracket.py             # Tournament standings and schedule view
└── tests/
    ├── test_combat.py             # Combat math, passive interactions
    └── test_tournament.py         # Round-robin logic, standings, tiebreakers
```

### Where things live

- **Game data** — `src/data/*.json` exclusively. Python files load and reference data; they never define stat numbers directly.
- **Entity state** — `src/entities/`. Entities hold data and expose simple methods; they do not contain system logic.
- **Logic** — `src/systems/`. Systems operate on entities but are not subclasses of them.
- **Screens** — `src/screens/`. Each screen owns its own state and exposes `update(dt)`, `draw(surface)`, `handle_event(event)`.
- **Constants** — `src/settings.py` only (resolution, FPS, colors, layout values).

---

## Coding Conventions

- **No hardcoded stats** — all weapon, armor, passive, and name data lives in `src/data/*.json`
- **dt-based movement** — `pos += velocity * dt`; never move by a fixed pixel count per frame
- **`pygame.Vector2`** for all 2-D positions and directions
- **`pygame.sprite.Sprite` / `Group`** for all renderable entities
- **Type hints** on all function signatures
- **Naming** — `UPPER_SNAKE_CASE` for constants, `PascalCase` for classes, `snake_case` for everything else
- **Screen size** — keep screen files under ~200 lines; extract to systems when they grow beyond that
- **Comments** — only where logic is non-obvious; no docstrings on self-evident methods
- **Tests** — combat math and tournament logic must have unit tests in `tests/`

---

## Current Development Status

**Early prototype — basic arena combat works; tournament and management systems not yet started.**

| Feature | Status |
|---------|--------|
| 800×600 window, 60 FPS loop, ESC/close quit | Done |
| Dark arena with title bar | Done |
| Base `Entity` class (move, target, attack, HP bar) | Done |
| `Gladiator` and `Enemy` placeholder types | Done |
| `ArenaScene` — prep / battle / victory / defeat states | Done |
| Escalating wave spawning (placeholder) | Done |
| Equipment slots on gladiators | Not started |
| Passive / power system | Not started |
| `Team` class with roster and gold | Not started |
| `Tournament` system — round-robin, standings | Not started |
| `Economy` system — gold, shop | Not started |
| AI team management between tournaments | Not started |
| Management screen (roster / shop UI) | Not started |
| Tournament bracket screen | Not started |
| JSON data files (weapons, armors, passives, names) | Not started |
| Gladiator lifecycle (injury, death, retirement) | Not started |
| Projectile entity (ranged attacks) | Not started |
| Sprite art and portraits | Not started |
| Audio (SFX + music) | Not started |
| Save / load | Not started |

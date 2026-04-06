import json
import os
import sys
import pygame

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from src.screens.main_menu        import MainMenuScreen
from src.screens.character_select import CharacterSelectScreen
from src.screens.town             import TownScreen
from src.screens.arena            import ArenaScreen
from src.entities.player          import Player
from src.entities.enemy           import Enemy
from src.systems.combat           import CombatResolver
from src.systems.limb_system      import LimbSystem
from src.systems.equipment        import EquipmentSystem

TOWN_START_GOLD = 150
MAX_DT          = 1 / 20   # cap to prevent spiral-of-death on lag spikes

_ENEMIES_PATH = os.path.join(os.path.dirname(__file__), "src", "data", "enemies.json")
_WEAPONS_PATH = os.path.join(os.path.dirname(__file__), "src", "data", "weapons.json")


def _load_enemy_for_stage(stage: int) -> Enemy:
    """Load the enemy entry that matches the given stage number."""
    with open(_ENEMIES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Find matching stage; fall back to last enemy if stage exceeds list
    entries = data["enemies"]
    entry = next((e for e in entries if e["stage"] == stage), entries[-1])
    return Enemy.from_dict(entry)


def _load_starting_weapon(weapon_id: str) -> dict:
    """Return the weapon dict for the given id from weapons.json."""
    with open(_WEAPONS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return next(w for w in data["weapons"] if w["id"] == weapon_id)


def _attach_limbs(entity) -> None:
    """Create and initialise a fresh LimbSystem on the entity."""
    limbs = LimbSystem()
    limbs.initialise()
    entity.limbs = limbs


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    equipment = EquipmentSystem()
    equipment.load()

    current = MainMenuScreen(screen)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, MAX_DT)

        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                current.handle_event(event)

        # ── Update ────────────────────────────────────────────────────────
        current.update(dt)

        # ── Draw ──────────────────────────────────────────────────────────
        current.draw()
        pygame.display.flip()

        # ── Screen transitions ────────────────────────────────────────────
        if not current.is_done():
            continue

        result = current.get_result()

        if isinstance(current, MainMenuScreen):
            if result == "quit":
                running = False
            elif result == "start":
                current = CharacterSelectScreen(screen)
            elif result == "settings":
                current = _settings_placeholder(screen)

        elif isinstance(current, CharacterSelectScreen):
            if result is None:
                current = MainMenuScreen(screen)
            else:
                player = Player(
                    name      = result["name"],
                    hp        = result["hp"],
                    stamina   = result["stamina"],
                    gold      = TOWN_START_GOLD,
                    strength  = result["strength"],
                    agility   = result["agility"],
                    endurance = result["endurance"],
                )
                # Equip starting weapon
                try:
                    weapon = _load_starting_weapon(result.get("starting_weapon", "iron_sword"))
                    player.equip_weapon(weapon)
                except (StopIteration, KeyError, FileNotFoundError):
                    pass
                _attach_limbs(player)
                current = TownScreen(screen, player, equipment=equipment, stage=player.stage)

        elif isinstance(current, TownScreen):
            player = current.player
            enemy  = _load_enemy_for_stage(player.stage)
            _attach_limbs(enemy)
            resolver = CombatResolver()
            current = ArenaScreen(screen, player, enemy, resolver)

        elif isinstance(current, ArenaScreen):
            player = current.player
            if current.player_won():
                # Award gold and advance stage
                reward = current.enemy.get_reward()
                player.earn_gold(reward["gold"])
                player.advance_stage()
                current = TownScreen(screen, player, equipment=equipment, stage=player.stage)
            else:
                current = _game_over_screen(screen)

        elif isinstance(current, _SettingsPlaceholder):
            current = MainMenuScreen(screen)

        elif isinstance(current, _GameOverScreen):
            if result == "retry":
                current = MainMenuScreen(screen)
            else:
                current = MainMenuScreen(screen)

    pygame.quit()
    sys.exit()


# ── Settings placeholder ──────────────────────────────────────────────────────

class _SettingsPlaceholder:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self._done   = False
        self._f_big  = pygame.font.SysFont(None, 56)
        self._f_hint = pygame.font.SysFont(None, 32)

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        self.surface.fill((15, 10, 8))
        msg  = self._f_big.render("Settings — Coming Soon", True, (180, 145, 55))
        hint = self._f_hint.render("Press ESC to go back", True, (100, 90, 70))
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        self.surface.blit(msg,  msg.get_rect(center=(W // 2, H // 2 - 30)))
        self.surface.blit(hint, hint.get_rect(center=(W // 2, H // 2 + 30)))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._done = True

    def is_done(self) -> bool:
        return self._done

    def get_result(self) -> None:
        return None


# ── Game Over screen ──────────────────────────────────────────────────────────

class _GameOverScreen:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self._done   = False
        self._f_big  = pygame.font.SysFont(None, 80)
        self._f_sub  = pygame.font.SysFont(None, 36)
        self._f_hint = pygame.font.SysFont(None, 28)

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        self.surface.fill((10, 6, 4))
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        title = self._f_big.render("GAME OVER", True, (200, 50, 50))
        sub   = self._f_sub.render("You have been defeated.", True, (130, 100, 80))
        hint  = self._f_hint.render("Press SPACE or ENTER to return to the main menu", True, (80, 70, 55))
        self.surface.blit(title, title.get_rect(center=(W // 2, H // 2 - 60)))
        self.surface.blit(sub,   sub.get_rect(center=(W // 2, H // 2 + 10)))
        self.surface.blit(hint,  hint.get_rect(center=(W // 2, H // 2 + 70)))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self._done = True

    def is_done(self) -> bool:
        return self._done

    def get_result(self) -> str:
        return "retry"


def _settings_placeholder(surface: pygame.Surface) -> _SettingsPlaceholder:
    return _SettingsPlaceholder(surface)


def _game_over_screen(surface: pygame.Surface) -> _GameOverScreen:
    return _GameOverScreen(surface)


if __name__ == "__main__":
    main()

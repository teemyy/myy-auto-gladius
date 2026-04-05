import sys
import pygame

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from src.screens.main_menu        import MainMenuScreen
from src.screens.character_select import CharacterSelectScreen
from src.screens.town             import TownScreen
from src.entities.player          import Player

TOWN_START_GOLD = 150
MAX_DT          = 1 / 20   # cap to prevent spiral-of-death on lag spikes


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

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
                # Player pressed ESC — go back to main menu
                current = MainMenuScreen(screen)
            else:
                # Confirmed character — create player and enter town
                player = Player(
                    name     = result["name"],
                    hp       = result["hp"],
                    stamina  = result["stamina"],
                    gold     = TOWN_START_GOLD,
                    strength = result["strength"],
                    agility  = result["agility"],
                )
                current = TownScreen(screen, player, equipment=None, stage=1)

        elif isinstance(current, TownScreen):
            # Arena not yet implemented — return to main menu for now
            current = MainMenuScreen(screen)

        elif isinstance(current, _SettingsPlaceholder):
            current = MainMenuScreen(screen)

    pygame.quit()
    sys.exit()


# ── Settings placeholder ──────────────────────────────────────────────────────

class _SettingsPlaceholder:
    """Minimal 'coming soon' screen for Settings."""

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


def _settings_placeholder(surface: pygame.Surface) -> _SettingsPlaceholder:
    return _SettingsPlaceholder(surface)


if __name__ == "__main__":
    main()

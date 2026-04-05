import pygame
from ..entities.gladiator import Gladiator
from ..entities.enemy import Enemy
from ..settings import (SCREEN_WIDTH, SCREEN_HEIGHT, ARENA_PADDING, TITLE_BAR_H,
                        DARK_BG, ARENA_FLOOR, ARENA_BORDER,
                        WHITE, GREEN, RED, YELLOW, TITLE)


class ArenaScene:
    """Main battle scene.  Call update(dt) and draw(surface) each frame."""

    WAVE_ENEMIES = 3   # enemies per wave

    def __init__(self):
        self.arena_rect = pygame.Rect(
            ARENA_PADDING,
            TITLE_BAR_H + ARENA_PADDING // 2,
            SCREEN_WIDTH  - ARENA_PADDING * 2,
            SCREEN_HEIGHT - TITLE_BAR_H - ARENA_PADDING,
        )
        self.font       = pygame.font.SysFont(None, 26)
        self.title_font = pygame.font.SysFont(None, 36)
        self.big_font   = pygame.font.SysFont(None, 56)
        self.wave      = 0
        self.state     = "prep"   # prep | battle | victory | defeat

        self.gladiators = pygame.sprite.Group()
        self.enemies    = pygame.sprite.Group()
        self._spawn_gladiators()

    # ------------------------------------------------------------------
    def _spawn_gladiators(self):
        self.gladiators.empty()
        cx = self.arena_rect.left + self.arena_rect.width // 4
        cy = self.arena_rect.centery
        spacing = 40
        for i in range(3):
            g = Gladiator(cx, cy + (i - 1) * spacing)
            self.gladiators.add(g)

    def _spawn_wave(self):
        self.enemies.empty()
        self.wave += 1
        count = self.WAVE_ENEMIES + self.wave - 1
        cx = self.arena_rect.right - self.arena_rect.width // 4
        cy = self.arena_rect.centery
        spacing = 40
        for i in range(count):
            offset = (i - count // 2) * spacing
            e = Enemy(cx, cy + offset)
            self.enemies.add(e)

    # ------------------------------------------------------------------
    def update(self, dt: float):
        if self.state == "prep":
            return
        if self.state != "battle":
            return

        enemy_list = [e for e in self.enemies if e.alive]
        glad_list  = [g for g in self.gladiators if g.alive]

        for g in glad_list:
            g.update(dt, enemy_list, self.arena_rect)
        for e in enemy_list:
            e.update(dt, glad_list, self.arena_rect)

        if not any(e.alive for e in self.enemies):
            self.state = "victory"
        elif not any(g.alive for g in self.gladiators):
            self.state = "defeat"

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if self.state == "prep" and event.key == pygame.K_SPACE:
                self._spawn_wave()
                self.state = "battle"
            elif self.state == "victory" and event.key == pygame.K_SPACE:
                self._spawn_gladiators()
                self.state = "prep"
            elif self.state == "defeat" and event.key == pygame.K_r:
                self.wave = 0
                self._spawn_gladiators()
                self.state = "prep"

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface):
        # Outer background
        surface.fill(DARK_BG)

        # Title bar
        title_surf = self.title_font.render(TITLE.upper(), True, (200, 170, 80))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, TITLE_BAR_H // 2))
        surface.blit(title_surf, title_rect)
        pygame.draw.line(surface, ARENA_BORDER, (0, TITLE_BAR_H - 1), (SCREEN_WIDTH, TITLE_BAR_H - 1), 2)

        # Arena floor + border
        pygame.draw.rect(surface, ARENA_FLOOR,  self.arena_rect)
        pygame.draw.rect(surface, ARENA_BORDER, self.arena_rect, 3)

        # Sprites
        for g in self.gladiators:
            surface.blit(g.image, g.rect)
            g.draw_healthbar(surface)
        for e in self.enemies:
            surface.blit(e.image, e.rect)
            e.draw_healthbar(surface)

        # HUD – wave counter (top-left inside arena)
        wave_surf = self.font.render(f"Wave {self.wave}", True, WHITE)
        surface.blit(wave_surf, (self.arena_rect.left + 8, self.arena_rect.top + 6))

        if self.state == "prep":
            self._draw_overlay(surface, "PRESS SPACE TO FIGHT", YELLOW)
        elif self.state == "victory":
            self._draw_overlay(surface, "VICTORY!  SPACE \u2192 next wave", GREEN)
        elif self.state == "defeat":
            self._draw_overlay(surface, "DEFEATED!  R \u2192 restart", RED)

    def _draw_overlay(self, surface, text, color):
        surf = self.big_font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, self.arena_rect.centery))
        surface.blit(surf, rect)

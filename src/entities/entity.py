import pygame
import math


class Entity(pygame.sprite.Sprite):
    """Base class for all combatants."""

    def __init__(self, x: float, y: float, hp: int, speed: float,
                 damage: int, attack_range: float, attack_cooldown: float,
                 color: tuple, radius: int = 14):
        super().__init__()
        self.pos = pygame.Vector2(x, y)
        self.max_hp = hp
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.attack_range = attack_range
        self.attack_cooldown = attack_cooldown
        self._cooldown_timer = 0.0
        self.alive = True

        self.radius = radius
        self.color = color
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    # ------------------------------------------------------------------
    def update(self, dt: float, targets: list, arena_rect: pygame.Rect):
        if not self.alive:
            return

        self._cooldown_timer = max(0.0, self._cooldown_timer - dt)

        target = self._nearest(targets)
        if target is None:
            return

        dist = self.pos.distance_to(target.pos)

        if dist > self.attack_range:
            self._move_toward(target, dt, arena_rect)
        elif self._cooldown_timer == 0.0:
            self._attack(target)

        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def _nearest(self, targets: list):
        living = [t for t in targets if t.alive]
        if not living:
            return None
        return min(living, key=lambda t: self.pos.distance_to(t.pos))

    def _move_toward(self, target, dt: float, arena_rect: pygame.Rect):
        direction = target.pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.pos += direction * self.speed * dt
        # Clamp inside arena
        self.pos.x = max(arena_rect.left + self.radius,
                         min(arena_rect.right  - self.radius, self.pos.x))
        self.pos.y = max(arena_rect.top  + self.radius,
                         min(arena_rect.bottom - self.radius, self.pos.y))

    def _attack(self, target):
        target.take_damage(self.damage)
        self._cooldown_timer = self.attack_cooldown

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False
            self.kill()

    # ------------------------------------------------------------------
    def draw_healthbar(self, surface: pygame.Surface):
        bar_w, bar_h = 28, 4
        x = int(self.pos.x) - bar_w // 2
        y = int(self.pos.y) - self.radius - 8
        pygame.draw.rect(surface, (80, 0, 0),   (x, y, bar_w, bar_h))
        filled = int(bar_w * self.hp / self.max_hp)
        pygame.draw.rect(surface, (0, 200, 60), (x, y, filled, bar_h))

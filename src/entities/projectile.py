from __future__ import annotations
import pygame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gladiator import Gladiator


class Projectile(pygame.sprite.Sprite):
    """A ranged projectile fired by a gladiator during combat.

    Created by the combat system when a gladiator with a ranged weapon (or the
    Multishot passive) makes an attack.  The arena screen renders all live
    projectiles each frame.
    """

    def __init__(
        self,
        owner: "Gladiator",
        start: pygame.Vector2,
        target: pygame.Vector2,
        speed: float,
        damage: int,
        radius: int = 5,
        color: tuple = (255, 220, 50),
    ):
        super().__init__()
        self.owner:   "Gladiator"   = owner
        self.pos:     pygame.Vector2 = pygame.Vector2(start)
        self.target:  pygame.Vector2 = pygame.Vector2(target)
        self.speed:   float          = speed
        self.damage:  int            = damage
        self.radius:  int            = radius
        self.color:   tuple          = color
        self.hit:     bool           = False  # True once it has connected

        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect  = self.image.get_rect(center=(int(start.x), int(start.y)))

    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Move the projectile toward its target position each frame."""
        pass

    def has_reached_target(self) -> bool:
        """Return True when the projectile is within one step of its target."""
        pass

    def redirect(self, new_target: pygame.Vector2) -> None:
        """Change the projectile's target mid-flight (e.g. homing passive)."""
        pass

    def __repr__(self) -> str:
        return (
            f"<Projectile owner={self.owner.name!r} "
            f"dmg={self.damage} hit={self.hit}>"
        )

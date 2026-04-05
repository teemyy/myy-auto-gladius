from .entity import Entity
from ..settings import (ENEMY_HP, ENEMY_SPEED, ENEMY_DAMAGE,
                        ENEMY_RANGE, ENEMY_COOLDOWN, RED)


class Enemy(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(
            x=x, y=y,
            hp=ENEMY_HP,
            speed=ENEMY_SPEED,
            damage=ENEMY_DAMAGE,
            attack_range=ENEMY_RANGE,
            attack_cooldown=ENEMY_COOLDOWN,
            color=RED,
        )
        self.team = "enemy"

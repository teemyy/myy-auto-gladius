import pygame
from .settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from .scenes.arena import ArenaScene

MAX_DT = 1 / 20  # cap at 50 ms to prevent spiral-of-death on lag spikes


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.scene = ArenaScene()

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, MAX_DT)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

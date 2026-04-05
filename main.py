import sys
import pygame

SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "Myy Auto Gladius"

DARK_BG   = ( 15,  10,   8)
GOLD_TEXT = (220, 175,  60)
GRAY      = (120, 120, 120)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    font_large  = pygame.font.SysFont(None, 72)
    font_small  = pygame.font.SysFont(None, 32)

    running = True
    while running:
        # ── Events ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ── Draw ─────────────────────────────────────────────────────────────
        screen.fill(DARK_BG)

        stage_surf = font_large.render("Stage 1", True, GOLD_TEXT)
        stage_rect = stage_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(stage_surf, stage_rect)

        hint_surf = font_small.render("ESC to quit", True, GRAY)
        hint_rect = hint_surf.get_rect(bottomright=(SCREEN_WIDTH - 16, SCREEN_HEIGHT - 12))
        screen.blit(hint_surf, hint_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

import pygame
import math
from classes import Player, Game, Bullet



def handle_events(game: Game, player: Player):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx, dy = mouse_x - player.x, mouse_y - player.y
            dist = math.hypot(dx, dy)
            if dist != 0:
                dx /= dist
                dy /= dist
                game.bullets.append(Bullet(player.x, player.y, dx, dy))
    return True

def run_game():
    pygame.init()

    info = pygame.display.Info()

    screen_width = int(info.current_w * 0.5)
    screen_height = int(info.current_h * 0.5)

    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Game")
    clock = pygame.time.Clock()

    game = Game(screen_width, screen_height)
    player = Player(game, 0, screen_width // 2, screen_height // 2)

    running = True
    while running:
        screen.fill((255, 255, 255))
        keys = pygame.key.get_pressed()
        player.move(keys)
        game.bullets = [b for b in game.bullets if not b.is_off_screen(game)]
        for bullet in game.bullets:
            bullet.update()
            bullet.draw(screen)

        player.draw(screen)


        running = handle_events(game, player)

        pygame.display.flip()

    pygame.quit()
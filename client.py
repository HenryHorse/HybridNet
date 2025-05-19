import socket
import threading
import time

import pygame
import json
import sys
import argparse
from server import start_server
from classes import Player, Bullet, Game

SERVER_IP = '127.0.0.1'
SERVER_PORT = 9999
FPS = 60

PLAYER_RADIUS = 20
BULLET_RADIUS = 10

game = Game()
state_lock = threading.Lock()

def receive_game_state(sock):
    buffer = ""
    while True:
        try:
            data = sock.recv(4096).decode()
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split("\n", 1)
                parsed = json.loads(line)
                with state_lock:
                    game.players = [Player.from_dict(p) for p in parsed["players"]]
                    game.bullets = [Bullet.from_dict(b) for b in parsed["bullets"]]
        except Exception as e:
            print(f"Error: {e}")
            break

def send_input(sock, keys, mouse_clicked):
    dx = 0
    dy = 0
    if keys[pygame.K_w]:
        dy -= 1
    if keys[pygame.K_s]:
        dy += 1
    if keys[pygame.K_a]:
        dx -= 1
    if keys[pygame.K_d]:
        dx += 1

    def send(msg):
        sock.sendall((json.dumps(msg) + "\n").encode())
    try:
        if dx != 0 or dy != 0:
            send({"move_vec": [dx, dy]})
        if mouse_clicked:
            mx, my = pygame.mouse.get_pos()
            send({"shoot": [mx, my]})
    except:
        pass

def draw_game(screen):
    screen.fill((255, 255, 255))
    font = pygame.font.SysFont(None, 24)
    with state_lock:
        for p in game.players:
            if not p.alive:
                continue
            pygame.draw.circle(screen, p.color, (int(p.x), int(p.y)), PLAYER_RADIUS)
            hp_text = font.render(str(p.health), True, (0, 0, 0))
            text_rect = hp_text.get_rect(center=(int(p.x), int(p.y) - PLAYER_RADIUS - 10))
            screen.blit(hp_text, text_rect)

        for b in game.bullets:
            pygame.draw.circle(screen, (0, 0, 0), (int(b.x), int(b.y)), BULLET_RADIUS)
    pygame.display.flip()

def run_client():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', action='store_true')
    args = parser.parse_args()
    if args.host:
        threading.Thread(target=start_server, daemon=True).start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_IP, SERVER_PORT))
    threading.Thread(target=receive_game_state, args=(sock,), daemon=True).start()

    pygame.init()
    screen = pygame.display.set_mode((game.screen_width, game.screen_height))
    pygame.display.set_caption('Multiplayer Client')
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True

        send_input(sock, keys, mouse_clicked)
        draw_game(screen)

    pygame.quit()
    sock.close()
    sys.exit()

if __name__ == '__main__':
    run_client()

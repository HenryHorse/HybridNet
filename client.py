import socket
import threading
import time
import requests
import pygame
import json
import sys
import argparse
from server import start_server
from classes import Player, Bullet, Game
from dotenv import load_dotenv
import os

SERVER_IP = '127.0.0.1'
SERVER_PORT = 9999
FPS = 60

PLAYER_RADIUS = 20
BULLET_RADIUS = 10

game = Game()
state_lock = threading.Lock()

load_dotenv()
SECRET_TOKEN = os.getenv('REMOTE_SERVER_TOKEN')

local_player_id = None
pending_inputs = []
input_sequence_number = 0

sock = None
receive_thread = None
is_hosting_locally = True
active_server_ip = "127.0.0.1"
just_migrated = False
migrate_frame_buffer = 0

def receive_game_state(current_sock):
    global active_server_ip, local_player_id, pending_inputs, sock, receive_thread

    buffer = ""
    while True:
        try:
            data = current_sock.recv(4096).decode()
            if not data:
                break
            buffer += data

            while '\n' in buffer:
                line, buffer = buffer.split("\n", 1)
                try:
                    parsed = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if "new_host" in parsed:
                    new_ip = parsed["new_host"]
                    print(f"Received migration notice: new host is {new_ip}")

                    try:
                        current_sock.close()
                    except:
                        pass

                    active_server_ip = new_ip
                    connect_to_server(new_ip)
                    return

                with state_lock:
                    received_players = [Player.from_dict(p) for p in parsed["players"]]
                    received_bullets = [Bullet.from_dict(b) for b in parsed["bullets"]]

                    if local_player_id is not None and local_player_id < len(received_players):
                        server_snapshot = received_players[local_player_id]

                        local_player = game.players.get(local_player_id)
                        if local_player is None:
                            local_player = server_snapshot
                        else:
                            local_player.x = server_snapshot.x
                            local_player.y = server_snapshot.y
                            local_player.health = server_snapshot.health
                            local_player.alive = server_snapshot.alive
                            local_player.respawn_timer = server_snapshot.respawn_timer

                        game.players.clear()
                        game.players[local_player_id] = local_player
                        for pid, player in enumerate(received_players):
                            if pid == local_player_id:
                                continue
                            game.players[pid] = player

                        game.bullets = received_bullets

                        for (seq, dx_i, dy_i) in pending_inputs:
                            local_player.move(dx_i, dy_i)

                        pending_inputs = []
                    else:
                        game.players.clear()
                        for pid, player in enumerate(received_players):
                            game.players[pid] = player
                        game.bullets = received_bullets

                        if local_player_id is None and len(received_players) > len(game.players):
                            local_player_id = len(received_players) - 1
        except Exception as e:
            print(f"Error: {e}")
            break

def send_input(sock, keys, mouse_clicked):
    global input_sequence_number, pending_inputs
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
        try:
            sock.sendall((json.dumps(msg) + "\n").encode())
        except:
            pass

    if dx != 0 or dy != 0:
        msg = {
            "move_vec": [dx, dy],
            "seq": input_sequence_number,
        }
        send(msg)

        with state_lock:
            if local_player_id is not None and local_player_id in game.players:
                game.players[local_player_id].move(dx, dy)
                pending_inputs.append((input_sequence_number, dx, dy))
        input_sequence_number += 1

    if mouse_clicked:
        mx, my = pygame.mouse.get_pos()
        send({"shoot": [mx, my]})


def draw_game(screen):
    screen.fill((255, 255, 255))
    font = pygame.font.SysFont(None, 24)
    with state_lock:
        for p in game.players.values():
            if not p.alive:
                continue
            pygame.draw.circle(screen, p.color, (int(p.x), int(p.y)), PLAYER_RADIUS)
            hp_text = font.render(str(p.health), True, (0, 0, 0))
            text_rect = hp_text.get_rect(center=(int(p.x), int(p.y) - PLAYER_RADIUS - 10))
            screen.blit(hp_text, text_rect)

        for b in game.bullets:
            pygame.draw.circle(screen, (0, 0, 0), (int(b.x), int(b.y)), BULLET_RADIUS)
    pygame.display.flip()

def start_remote_server():
    headers = {
        "Authorization": f"Bearer {SECRET_TOKEN}"
    }
    response = requests.post("http://100.91.195.61:9998/start", headers=headers)
    print(response.json())

def connect_to_server(ip):
    global sock, receive_thread
    try:
        if sock:
            sock.close()
    except:
        pass
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, SERVER_PORT))
    receive_thread = threading.Thread(target=receive_game_state, args=(sock,), daemon=True)
    receive_thread.start()


def migrate_to_remote():
    global is_hosting_locally, active_server_ip, just_migrated, migrate_frame_buffer

    REMOTE_IP = "100.91.195.61"

    try:
        migrate_msg = {"migrate": REMOTE_IP}
        sock.sendall((json.dumps(migrate_msg) + "\n").encode())
        print(f"Sent migrate request to server: {migrate_msg}")
    except Exception as e:
        print(f"Could not send migrate request to server: {e}")

    time.sleep(0.1)
    try:
        sock.close()
    except:
        pass
    start_remote_server()
    is_hosting_locally = False
    active_server_ip = REMOTE_IP
    connect_to_server(active_server_ip)

    just_migrated = True
    migrate_frame_buffer = 10

def run_client():
    global migrate_frame_buffer, is_hosting_locally, active_server_ip
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', action='store_true')
    parser.add_argument('--ip', type=str, default='127.0.0.1')
    args = parser.parse_args()

    active_server_ip = args.ip


    if args.host:
        is_hosting_locally = True
        threading.Thread(target=start_server, daemon=True).start()
        connect_to_server("127.0.0.1")
    else:
        is_hosting_locally = False
        connect_to_server(args.ip)



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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and is_hosting_locally:
                    print("Transferring host to remote server...")
                    migrate_to_remote()

        send_input(sock, keys, mouse_clicked)
        draw_game(screen)

    pygame.quit()
    sock.close()
    sys.exit()



if __name__ == '__main__':
    run_client()
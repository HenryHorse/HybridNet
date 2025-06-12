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

REMOTE_IP = "100.91.195.61"
SERVER_IP = '127.0.0.1'
SERVER_PORT = 9999
FPS = 60

PLAYER_RADIUS = 20
BULLET_RADIUS = 10

game = Game()
state_lock = threading.Lock()

load_dotenv()
SECRET_TOKEN = os.getenv('REMOTE_SERVER_TOKEN')

sock = None
receive_thread = None
is_hosting_locally = True
active_server_ip = "127.0.0.1"
just_migrated = False

original_host_ip = None
has_migrated = False
server_thread = None

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
                    game.players.clear()
                    for p in parsed["players"]:
                        player = Player.from_dict(p)
                        game.players[player.id] = player
                    game.bullets = [Bullet.from_dict(b) for b in parsed["bullets"]]
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
        }
        send(msg)


    if mouse_clicked:
        mx, my = pygame.mouse.get_pos()
        send({"shoot": [mx, my]})


def draw_game(screen):
    screen.fill((173, 216, 230))
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
    response = requests.post(f"http://{REMOTE_IP}:9998/start", headers=headers)
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


def toggle_host():
    global is_hosting_locally, active_server_ip, just_migrated, has_migrated, original_host_ip, server_thread



    if not has_migrated:
        print("Migrating to remote server...")
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
        has_migrated = True
    else:
        print("Migrating back to original host...")
        try:
            migrate_msg = {"migrate": original_host_ip}
            sock.sendall((json.dumps(migrate_msg) + "\n").encode())
            print(f"Sent migrate request to server: {migrate_msg}")
        except Exception as e:
            print(f"Could not send migrate request to server: {e}")

        time.sleep(0.1)
        try:
            sock.close()
        except:
            pass

        connect_to_server(original_host_ip)
        active_server_ip = original_host_ip
        is_hosting_locally = True
        has_migrated = False


def run_client():
    global is_hosting_locally, active_server_ip, original_host_ip
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', action='store_true')
    parser.add_argument('--ip', type=str, default='127.0.0.1')
    args = parser.parse_args()

    original_host_ip = args.ip
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
                if event.key == pygame.K_SPACE:
                    print("Transferring host")
                    toggle_host()

        send_input(sock, keys, mouse_clicked)
        draw_game(screen)

    pygame.quit()
    sock.close()
    sys.exit()



if __name__ == '__main__':
    run_client()
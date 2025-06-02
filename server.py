import socket
import threading
import json
import math
import time
from classes import Player, Game, Bullet, BULLET_RADIUS, PLAYER_RADIUS

HOST = '0.0.0.0'
PORT = 9999

FPS = 60

clients = []
lock = threading.Lock()

def normalize(dx, dy):
    dist = math.hypot(dx, dy)
    if dist != 0:
        dx /= dist
        dy /= dist
    return dx, dy

def handle_client(connection, address, game: Game, player_id):
    print(f"Client {player_id} connected from {address}.")
    buffer = ""
    with lock:
        game.players[player_id] = Player(player_id, 300, 300, game.screen_width, game.screen_height)

    try:
        while True:
            data = connection.recv(1024).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                with lock:
                    player = game.players[player_id]
                    if not player or not player.alive:
                        continue
                    if "move_vec" in msg:
                        dx, dy = msg["move_vec"]
                        player.move(dx, dy)
                    if "shoot" in msg:
                        mx, my = msg["shoot"]
                        dx, dy = normalize(mx - player.x, my - player.y)
                        game.bullets.append(Bullet(player.x, player.y, dx, dy, player_id))

    finally:
        print(f"Client {player_id} disconnected from {address}.")
        with lock:
            game.players.pop(player_id, None)
        connection.close()

def game_loop(game: Game):
    while True:
        with lock:
            for b in game.bullets:
                b.update()
            bullets_kept = []
            for b in game.bullets:
                hit = False
                for pid, player in game.players.items():
                    if pid == b.owner_id:
                        continue
                    if (b.x - player.x) ** 2 + (b.y - player.y) ** 2 < (PLAYER_RADIUS + BULLET_RADIUS) ** 2:
                        player.health -= 20
                        if player.health <= 0:
                            player.alive = False
                            player.respawn_timer = 3 * FPS
                        hit = True
                        break
                if not hit and not b.is_off_screen(game):
                    bullets_kept.append(b)

            game.bullets = bullets_kept

            for player in game.players.values():
                if not player.alive:
                    player.respawn_timer -= 1
                    if player.respawn_timer <= 0:
                        player.health = 100
                        player.alive = True
                        player.x = 300
                        player.y = 300


            state = json.dumps({
                "players": [p.to_dict() for p in game.players.values()],
                "bullets": [b.to_dict() for b in game.bullets]
            })

            for connection in clients:
                try:
                    connection.sendall(state.encode() + b'\n')
                except:
                    continue
        time.sleep(1 / FPS)


def start_server():
    game = Game()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Listening on {HOST}:{PORT}")
    threading.Thread(target=game_loop, args=(game,), daemon=True).start()

    player_id = 0
    while True:
        connection, address = server.accept()
        clients.append(connection)
        threading.Thread(target=handle_client, args=(connection, address, game, player_id), daemon=True).start()
        player_id += 1


if __name__ == '__main__':
    start_server()
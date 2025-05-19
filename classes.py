PLAYER_SPEED = 10
PLAYER_RADIUS = 20
BULLET_SPEED = 5
BULLET_RADIUS = 10

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

class Game:
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.players = {}
        self.bullets = []

class Player:
    def __init__(self, id, x, y, screen_width, screen_height, color=(0, 0, 0), health=100, alive=True, respawn_timer=0):
        self.id = id
        self.x = x
        self.y = y
        self.color = color
        self.health = health
        self.alive = alive
        self.respawn_timer = respawn_timer
        self.screen_width = screen_width
        self.screen_height = screen_height

    def move(self, dx, dy):
        magnitude = (dx ** 2 + dy ** 2) ** 0.5
        if magnitude > 0:
            dx = dx / magnitude * PLAYER_SPEED
            dy = dy / magnitude * PLAYER_SPEED

            self.x += dx
            self.y += dy

            self.x = max(PLAYER_RADIUS, min(self.x, self.screen_width - PLAYER_RADIUS))
            self.y = max(PLAYER_RADIUS, min(self.y, self.screen_height - PLAYER_RADIUS))

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "health": self.health,
            "alive": self.alive,
            "respawn_timer": self.respawn_timer
        }

    @staticmethod
    def from_dict(data):
        return Player(
            data["id"], data["x"], data["y"],
            SCREEN_WIDTH, SCREEN_HEIGHT,
            tuple(data["color"]),
            data["health"],
            data["alive"],
            data["respawn_timer"]
        )

    # def draw(self, screen):
    #     pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), PLAYER_RADIUS)


class Bullet:
    def __init__(self, x, y, dx, dy, owner_id = None):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.owner_id = owner_id

    def update(self):
        self.x += self.dx * BULLET_SPEED
        self.y += self.dy * BULLET_SPEED

    # def draw(self, screen):
    #     pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), BULLET_RADIUS)

    def is_off_screen(self, game):
        return (self.x < 0
                or self.x > game.screen_width
                or self.y < 0
                or self.y > game.screen_height)

    def to_dict(self):
        return {"x": float(self.x), "y": float(self.y), "dx": self.dx, "dy": self.dy, "owner_id": self.owner_id}

    @staticmethod
    def from_dict(data):
        return Bullet(data["x"], data["y"], data["dx"], data["dy"], data.get("owner_id"))

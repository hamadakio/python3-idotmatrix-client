import math
import random
from PIL import Image, ImageDraw


# -------------------------------------------------------------
# 1. CLOCK STYLES CATALOG
# -------------------------------------------------------------
CLOCK_FACES = [
    {
        "id": 0,
        "name": "Padrão Digital",
        "category": "Minimalista",
        "description": "Relógio digital clean e moderno com alta legibilidade.",
        "icon": "🕒",
        "default_color": (0, 229, 255),
    },
    {
        "id": 1,
        "name": "Natal Festivo",
        "category": "Temático",
        "description": "Edição comemorativa natalina com detalhes festivos.",
        "icon": "🎄",
        "default_color": (255, 68, 68),
    },
    {
        "id": 2,
        "name": "Velocímetro Racing",
        "category": "Esportivo",
        "description": "Layout esportivo inspirado em cockpits de corrida.",
        "icon": "🏎️",
        "default_color": (255, 170, 0),
    },
    {
        "id": 3,
        "name": "Invertido Alto Contraste",
        "category": "Contraste",
        "description": "Fundo iluminado com dígitos invertidos em alto contraste.",
        "icon": "⬛",
        "default_color": (255, 255, 255),
    },
    {
        "id": 4,
        "name": "Ampulheta Animada",
        "category": "Retrô 8-Bit",
        "description": "Ampulheta retrô com areia caindo em tempo real.",
        "icon": "⏳",
        "default_color": (255, 235, 59),
    },
    {
        "id": 5,
        "name": "Moldura Neon 1",
        "category": "Cyberpunk",
        "description": "Borda neon envolvente com estilo synthwave.",
        "icon": "🔲",
        "default_color": (124, 77, 255),
    },
    {
        "id": 6,
        "name": "Moldura Técnica 2",
        "category": "Sci-Fi",
        "description": "Moldura com marcadores futuristas e estética industrial.",
        "icon": "💠",
        "default_color": (0, 230, 118),
    },
    {
        "id": 7,
        "name": "Moldura Arcade 3",
        "category": "Games",
        "description": "Moldura estilo fliperama clássico com cantos vivos.",
        "icon": "👾",
        "default_color": (233, 30, 99),
    },
]


# -------------------------------------------------------------
# 2. PIXEL ART FEED & PRESETS (32x32 generators)
# -------------------------------------------------------------
def create_heart_art(size=32) -> Image.Image:
    img = Image.new("RGB", (size, size), (15, 10, 20))
    draw = ImageDraw.Draw(img)
    # Heart pixel shape
    c_red = (255, 40, 90)
    c_hi = (255, 150, 180)
    draw.rectangle([6, 8, 14, 15], fill=c_red)
    draw.rectangle([17, 8, 25, 15], fill=c_red)
    draw.rectangle([4, 11, 27, 18], fill=c_red)
    draw.polygon([(4, 18), (27, 18), (16, 28)], fill=c_red)
    # Highlight
    draw.rectangle([8, 10, 11, 13], fill=c_hi)
    return img


def create_mush_art(size=32) -> Image.Image:
    img = Image.new("RGB", (size, size), (10, 15, 25))
    draw = ImageDraw.Draw(img)
    # Mushroom Cap
    draw.ellipse([5, 6, 26, 21], fill=(244, 67, 54))
    # Spots
    draw.ellipse([12, 8, 19, 14], fill=(255, 255, 255))
    draw.ellipse([6, 12, 10, 18], fill=(255, 255, 255))
    draw.ellipse([21, 12, 25, 18], fill=(255, 255, 255))
    # Stem
    draw.rectangle([10, 19, 21, 26], fill=(255, 236, 179))
    draw.line([13, 21, 13, 24], fill=(60, 60, 60))
    draw.line([18, 21, 18, 24], fill=(60, 60, 60))
    return img


def create_invader_art(size=32) -> Image.Image:
    img = Image.new("RGB", (size, size), (5, 5, 12))
    draw = ImageDraw.Draw(img)
    c = (0, 255, 180)
    # Space Invader pixel blocks
    pattern = [
        "   1      1   ",
        "    1    1    ",
        "   11111111   ",
        "  11 1111 11  ",
        " 111111111111 ",
        " 1 11111111 1 ",
        " 1 1      1 1 ",
        "    11  11    ",
    ]
    off_x, off_y = 9, 12
    for r, row in enumerate(pattern):
        for col, ch in enumerate(row):
            if ch == "1":
                draw.point((off_x + col, off_y + r), fill=c)
    return img


def create_skull_art(size=32) -> Image.Image:
    img = Image.new("RGB", (size, size), (12, 10, 18))
    draw = ImageDraw.Draw(img)
    neon = (170, 0, 255)
    # Skull crown
    draw.ellipse([8, 6, 23, 20], fill=neon)
    draw.rectangle([10, 16, 21, 24], fill=neon)
    # Eyes
    draw.rectangle([11, 13, 14, 16], fill=(12, 10, 18))
    draw.rectangle([17, 13, 20, 16], fill=(12, 10, 18))
    # Teeth
    for x in range(12, 20, 2):
        draw.line([x, 22, x, 24], fill=(12, 10, 18))
    return img


def create_coffee_art(size=32) -> Image.Image:
    img = Image.new("RGB", (size, size), (20, 15, 10))
    draw = ImageDraw.Draw(img)
    # Steam
    draw.line([13, 5, 14, 8], fill=(180, 160, 140))
    draw.line([18, 4, 17, 7], fill=(180, 160, 140))
    # Cup
    draw.rectangle([9, 12, 22, 24], fill=(255, 255, 255))
    draw.rectangle([11, 14, 20, 16], fill=(109, 76, 65))
    # Handle
    draw.arc([19, 14, 25, 21], 270, 90, fill=(255, 255, 255))
    return img


def create_notification_art(app_name: str, size=32) -> Image.Image:
    """Renders official style app badges for matrix alerts."""
    img = Image.new("RGB", (size, size), (10, 12, 18))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 31, 31], outline=(30, 40, 60))

    if app_name == "WhatsApp":
        draw.ellipse([7, 7, 24, 24], fill=(37, 211, 102))
        draw.polygon([(7, 20), (5, 26), (12, 23)], fill=(37, 211, 102))
        draw.rectangle([12, 12, 19, 19], fill=(255, 255, 255))
    elif app_name == "Instagram":
        draw.rounded_rectangle([7, 7, 24, 24], radius=4, fill=(225, 48, 108))
        draw.rectangle([9, 9, 22, 22], outline=(255, 255, 255))
        draw.ellipse([13, 13, 18, 18], outline=(255, 255, 255))
        draw.point((20, 11), fill=(255, 255, 255))
    elif app_name == "Discord":
        draw.rounded_rectangle([6, 8, 25, 23], radius=4, fill=(88, 101, 242))
        draw.ellipse([10, 13, 13, 16], fill=(255, 255, 255))
        draw.ellipse([18, 13, 21, 16], fill=(255, 255, 255))
    elif app_name == "Email":
        draw.rectangle([6, 9, 25, 22], fill=(66, 133, 244))
        draw.line([(6, 9), (15, 17), (25, 9)], fill=(255, 255, 255))
    else:
        # Telephone / Call
        draw.rounded_rectangle([7, 7, 24, 24], radius=5, fill=(76, 175, 80))
        draw.ellipse([11, 11, 20, 20], fill=(255, 255, 255))

    return img


FEED_PRESETS = [
    {"name": "Coração Pulsante", "category": "Neon & Cyber", "render": create_heart_art, "icon": "💖"},
    {"name": "Super Cogumelo", "category": "Retro Games", "render": create_mush_art, "icon": "🍄"},
    {"name": "Space Invader", "category": "Retro Games", "render": create_invader_art, "icon": "👾"},
    {"name": "Neon Skull", "category": "Neon & Cyber", "render": create_skull_art, "icon": "💀"},
    {"name": "Café & Foco", "category": "Dia a Dia", "render": create_coffee_art, "icon": "☕"},
]


# -------------------------------------------------------------
# 3. RELAXING WHITE NOISE & SOUND PATTERNS
# -------------------------------------------------------------
def render_sound_eq_frame(bars: list, size=32) -> Image.Image:
    """Renders audio equalizer frequency bars on 32x32 matrix."""
    img = Image.new("RGB", (size, size), (8, 10, 16))
    draw = ImageDraw.Draw(img)

    num_bars = len(bars)
    bar_width = max(1, size // num_bars)

    for i, val in enumerate(bars):
        # val is 0.0 to 1.0
        h = int(val * (size - 4))
        x = i * bar_width
        y1 = size - 2 - h
        y2 = size - 2

        # Gradient color based on height
        for y in range(y1, y2):
            progress = 1.0 - ((y - y1) / max(1, h))
            if progress > 0.7:
                c = (255, 50, 80)
            elif progress > 0.4:
                c = (255, 200, 30)
            else:
                c = (0, 229, 255)
            draw.line([x, y, x + bar_width - 1, y], fill=c)

    return img


def render_campfire_pattern(tick: int, size=32) -> Image.Image:
    """Cozy campfire animation frame."""
    img = Image.new("RGB", (size, size), (10, 6, 8))
    draw = ImageDraw.Draw(img)
    # Logs
    draw.line([8, 27, 24, 27], fill=(100, 60, 40), width=2)
    # Fire base
    for x in range(10, 22):
        flame_h = random.randint(8, 18) + int(math.sin((tick + x) * 0.5) * 4)
        c = (255, random.randint(50, 150), 20)
        draw.line([x, 26, x, max(6, 26 - flame_h)], fill=c)
        if flame_h > 12:
            draw.line([x, 26, x, 26 - flame_h + 5], fill=(255, 235, 59))
    return img


def render_ocean_waves_pattern(tick: int, size=32) -> Image.Image:
    """Calm ocean waves animation frame."""
    img = Image.new("RGB", (size, size), (6, 12, 24))
    draw = ImageDraw.Draw(img)
    # Moon
    draw.ellipse([22, 4, 28, 10], fill=(240, 245, 255))
    # Wave layers
    for y_base, c in [(20, (13, 71, 161)), (24, (21, 101, 192)), (28, (30, 136, 229))]:
        points = []
        for x in range(size):
            y = y_base + int(math.sin((x * 0.3) + (tick * 0.2)) * 2)
            points.append((x, y))
        for x, y in points:
            draw.line([x, y, x, size - 1], fill=c)
    return img


# -------------------------------------------------------------
# 4. RETRO MINI-GAME: SNAKE ENGINE FOR MATRIX
# -------------------------------------------------------------
class SnakeGameEngine:
    """Complete Snake game engine running in matrix coordinates."""
    def __init__(self, grid_size=32):
        self.grid_size = grid_size
        self.reset()

    def reset(self):
        mid = self.grid_size // 2
        self.snake = [(mid, mid), (mid - 1, mid), (mid - 2, mid)]
        self.direction = (1, 0) # Right
        self.food = self._spawn_food()
        self.score = 0
        self.game_over = False

    def _spawn_food(self):
        while True:
            fx = random.randint(1, self.grid_size - 2)
            fy = random.randint(1, self.grid_size - 2)
            if (fx, fy) not in self.snake:
                return (fx, fy)

    def change_direction(self, dx, dy):
        # Prevent 180 degree turns
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.direction = (dx, dy)

    def step(self):
        if self.game_over:
            return

        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % self.grid_size, (head_y + dy) % self.grid_size)

        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 10
            self.food = self._spawn_food()
        else:
            self.snake.pop()

    def render(self) -> Image.Image:
        img = Image.new("RGB", (self.grid_size, self.grid_size), (8, 10, 16))
        draw = ImageDraw.Draw(img)

        # Border
        draw.rectangle([0, 0, self.grid_size - 1, self.grid_size - 1], outline=(30, 35, 50))

        # Food
        fx, fy = self.food
        draw.point((fx, fy), fill=(255, 50, 50))

        # Snake Body
        for i, (bx, by) in enumerate(self.snake):
            color = (0, 255, 180) if i == 0 else (0, 180, 120)
            draw.point((bx, by), fill=color)

        if self.game_over:
            # Red flash border
            draw.rectangle([0, 0, self.grid_size - 1, self.grid_size - 1], outline=(255, 0, 0))

        return img

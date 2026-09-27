"""Централна конфигурация на играта.

Тук са ВСИЧКИ константи: размери, цветове, клавиши и баланс. Модулът не импортира pygame,
затова може да се ползва и от логическите модули, и от тестовете.
"""

from __future__ import annotations

from dataclasses import dataclass

Color = tuple[int, int, int]

# ---------------------------------------------------------------------------
# Прозорец и рендериране
# ---------------------------------------------------------------------------
WINDOW_TITLE = "Roguelike – Подземията на краля"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

TILE_SIZE = 32
PANEL_HEIGHT = 144  # долният панел с HUD и лог
PANEL_PADDING = 8
HUD_WIDTH = 320              # лявата част на панела (статистики); вдясно е логът
BAR_HEIGHT = 18

# Колко тайла се виждат на екрана (камерата показва този "прозорец" от картата).
VIEW_WIDTH_TILES = SCREEN_WIDTH // TILE_SIZE
VIEW_HEIGHT_TILES = (SCREEN_HEIGHT - PANEL_HEIGHT) // TILE_SIZE

FONT_SIZE_TILE = 30
FONT_SIZE_UI = 20
FONT_SIZE_MENU = 28
FONT_SIZE_TITLE = 56

# ---------------------------------------------------------------------------
# Карта
# ---------------------------------------------------------------------------
MAP_WIDTH = 80
MAP_HEIGHT = 45
FOV_RADIUS = 8
BOSS_FLOOR = 10              # последният етаж – там е финалният бос

# ---------------------------------------------------------------------------
# Цветове (R, G, B)
# ---------------------------------------------------------------------------
COLOR_BLACK: Color = (0, 0, 0)
COLOR_WHITE: Color = (255, 255, 255)
COLOR_GRAY: Color = (128, 128, 128)
COLOR_TITLE: Color = (255, 200, 60)
COLOR_MENU_TEXT: Color = (220, 220, 220)
COLOR_MENU_SELECTED: Color = (255, 220, 90)
COLOR_PANEL_BG: Color = (18, 18, 26)
COLOR_PANEL_BORDER: Color = (70, 70, 90)
COLOR_HP_BAR_FULL: Color = (60, 170, 60)
COLOR_HP_BAR_EMPTY: Color = (90, 25, 25)
COLOR_GAME_OVER: Color = (200, 30, 30)

COLOR_PLAYER: Color = (255, 255, 255)

# Тайлове: (цвят на фона, цвят на символа) – светли (видими) и тъмни (изследвани).
COLOR_WALL_LIGHT_BG: Color = (110, 90, 60)
COLOR_WALL_LIGHT_FG: Color = (160, 140, 100)
COLOR_WALL_DARK_BG: Color = (40, 36, 48)
COLOR_WALL_DARK_FG: Color = (65, 60, 75)
COLOR_FLOOR_LIGHT_BG: Color = (60, 55, 45)
COLOR_FLOOR_LIGHT_FG: Color = (110, 100, 80)
COLOR_FLOOR_DARK_BG: Color = (22, 22, 32)
COLOR_FLOOR_DARK_FG: Color = (45, 45, 60)
COLOR_STAIRS_LIGHT_FG: Color = (255, 255, 120)
COLOR_STAIRS_DARK_FG: Color = (110, 110, 60)

# ---------------------------------------------------------------------------
# Клавиши (имена както ги връща pygame.key.name; главни букви – чрез event.unicode)
# ---------------------------------------------------------------------------
MOVE_KEYS: dict[str, tuple[int, int]] = {
    # стрелки
    "up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0),
    "home": (-1, -1), "page up": (1, -1), "end": (-1, 1), "page down": (1, 1),
    # WASD + диагонали Q/E/Z/C
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
    "q": (-1, -1), "e": (1, -1), "z": (-1, 1), "c": (1, 1),
    # numpad
    "[8]": (0, -1), "[2]": (0, 1), "[4]": (-1, 0), "[6]": (1, 0),
    "[7]": (-1, -1), "[9]": (1, -1), "[1]": (-1, 1), "[3]": (1, 1),
}
WAIT_KEYS: frozenset[str] = frozenset({".", "space", "[5]"})
CONFIRM_KEYS: frozenset[str] = frozenset({"return", "enter"})
ESCAPE_KEY = "escape"
DESCEND_CHAR = ">"
MENU_UP_KEYS: frozenset[str] = frozenset({"up", "w", "[8]"})
MENU_DOWN_KEYS: frozenset[str] = frozenset({"down", "s", "[2]"})

# ---------------------------------------------------------------------------
# Случайност
# ---------------------------------------------------------------------------
SEED_MAX = 2**31 - 1

# ---------------------------------------------------------------------------
# BSP генератор
# ---------------------------------------------------------------------------
BSP_MIN_LEAF_SIZE = 10       # листо по-малко от 2x това не се дели повече
BSP_MAX_DEPTH = 5            # максимална дълбочина на дървото
BSP_SPLIT_MIN = 0.4          # точката на деление е между 40% ...
BSP_SPLIT_MAX = 0.6          # ... и 60% от размера
BSP_ASPECT_RATIO = 1.25      # над това съотношение режем по-дългата страна
BSP_ROOM_MIN_SIZE = 5
BSP_ROOM_MAX_SIZE = 14
BSP_ROOM_MARGIN = 1          # отстъп на стаята от ръба на листото

# ---------------------------------------------------------------------------
# Cellular Automata генератор
# ---------------------------------------------------------------------------
CA_WALL_PROBABILITY = 0.45       # начален процент стени
CA_ITERATIONS = 5                # брой итерации на правилото
CA_EMPTY_FILL_ITERATIONS = 2     # в първите N итерации "0 стени" също дава стена
CA_WALL_THRESHOLD = 5            # ≥ толкова стени в 3x3 → стена
CA_MIN_FLOOR_RATIO = 0.40        # най-големият регион трябва да е ≥ 40% от площта
CA_MAX_ATTEMPTS = 100            # максимум опити, преди да се откажем
CA_SAFE_RADIUS = 6               # радиус без врагове около старта в пещера

# ---------------------------------------------------------------------------
# Играч
# ---------------------------------------------------------------------------
PLAYER_NAME = "Играч"
PLAYER_CHAR = "@"
PLAYER_MAX_HP = 30
PLAYER_ATTACK = 5
PLAYER_DEFENSE = 1

CORPSE_CHAR = "%"
COLOR_CORPSE: Color = (140, 20, 20)

# ---------------------------------------------------------------------------
# Бой и AI
# ---------------------------------------------------------------------------
DAMAGE_VARIANCE = 1          # щетата варира с ±1
CRIT_CHANCE = 0.05           # 5% шанс за критичен удар
CRIT_MULTIPLIER = 2
MISS_CHANCE = 0.05           # 5% шанс за пропуск
AI_MEMORY_TURNS = 5          # колко хода врагът помни къде е видял играча
PATH_OCCUPIED_COST = 10      # A*: допълнителна цена за клетка, заета от друго същество

# ---------------------------------------------------------------------------
# Лог на съобщенията
# ---------------------------------------------------------------------------
LOG_MAX_MESSAGES = 300
LOG_PANEL_LINES = 6
COLOR_MSG_DEFAULT: Color = (220, 220, 220)
COLOR_MSG_PLAYER_ATTACK: Color = (225, 225, 225)
COLOR_MSG_ENEMY_ATTACK: Color = (255, 150, 150)
COLOR_MSG_CRIT: Color = (255, 170, 60)
COLOR_MSG_MISS: Color = (150, 150, 150)
COLOR_MSG_ENEMY_DIE: Color = (255, 110, 60)
COLOR_MSG_PLAYER_DIE: Color = (255, 40, 40)
COLOR_MSG_WELCOME: Color = (120, 180, 255)
COLOR_MSG_DESCEND: Color = (200, 160, 255)
COLOR_MSG_IMPOSSIBLE: Color = (140, 140, 140)


# ---------------------------------------------------------------------------
# Врагове
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EnemyDef:
    """Описание на тип враг (данни, не логика)."""

    name: str
    char: str
    color: Color
    hp: int
    attack: int
    defense: int
    xp: int
    ai: str               # "hostile", "ranged" или "boss"
    regen: int = 0        # HP на ход


ENEMIES: dict[str, EnemyDef] = {
    "rat": EnemyDef("Плъх", "r", (170, 140, 110), hp=4, attack=2, defense=0, xp=5,
                    ai="hostile"),
    "goblin": EnemyDef("Гоблин", "g", (90, 190, 70), hp=10, attack=4, defense=1, xp=20,
                       ai="hostile"),
}

# Тегла за спаунване: {име: {от_етаж: тегло}} – важи последният праг ≤ текущия етаж.
ENEMY_SPAWN_WEIGHTS: dict[str, dict[int, int]] = {
    "rat": {1: 60, 4: 20, 7: 5},
    "goblin": {1: 35, 3: 45, 6: 30},
}
# Максимален брой врагове на етаж: {от_етаж: брой}.
MAX_ENEMIES_BY_FLOOR: dict[int, int] = {1: 5, 3: 7, 5: 9, 7: 11, 9: 13}

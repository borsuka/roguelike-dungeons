"""Централна конфигурация на играта.

Тук са ВСИЧКИ константи: размери, цветове, клавиши и баланс. Модулът не импортира pygame,
затова може да се ползва и от логическите модули, и от тестовете.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
MENU_BOX_WIDTH = 560

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
DROP_CHAR = "D"
INVENTORY_KEY = "i"
PICKUP_KEY = "g"
LOG_KEY = "v"
PAGE_UP_KEYS: frozenset[str] = frozenset({"page up", "[9]"})
PAGE_DOWN_KEYS: frozenset[str] = frozenset({"page down", "[3]"})
HELP_LINES: tuple[str, ...] = (
    "Движение/атака: стрелки, WASD+QEZC, numpad    Чакай: . или Space    Вдигни: G",
    "Инвентар: I    Изхвърли: Shift+D    Слез: > или Enter    Лог: V    Пауза: Esc",
)
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
BOSS_ARENA_SPLIT = 0.45      # етаж 10: левите 45% са обикновено BSP, вдясно е залата
BOSS_ARENA_WIDTH = 30
BOSS_ARENA_HEIGHT = 25

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
PLAYER_MAX_HP = 40
PLAYER_ATTACK = 5
PLAYER_DEFENSE = 1

CORPSE_CHAR = "%"
COLOR_CORPSE: Color = (140, 20, 20)

# Прогресия: XP за следващо ниво = LEVEL_UP_BASE * ниво * LEVEL_UP_FACTOR
LEVEL_UP_BASE = 35
LEVEL_UP_FACTOR = 1.5
LEVEL_UP_HP = 20
LEVEL_UP_ATTACK = 1
LEVEL_UP_DEFENSE = 1

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
COLOR_MSG_HEAL: Color = (100, 230, 100)
COLOR_MSG_MAGIC: Color = (190, 140, 255)
COLOR_MSG_ITEM: Color = (240, 220, 140)
COLOR_MSG_XP: Color = (130, 220, 255)
COLOR_MSG_LEVEL_UP: Color = (255, 230, 100)
COLOR_MSG_BOSS: Color = (255, 90, 30)
COLOR_VICTORY: Color = (255, 215, 0)
COLOR_XP_BAR_FULL: Color = (70, 130, 220)
COLOR_XP_BAR_EMPTY: Color = (30, 35, 70)
COLOR_CURSOR: Color = (255, 255, 0)
COLOR_MENU_BOX_BG: Color = (25, 25, 38)


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
    "skeleton_archer": EnemyDef("Скелет стрелец", "s", (225, 225, 205), hp=8, attack=3,
                                defense=1, xp=30, ai="ranged"),
    "orc": EnemyDef("Орк", "o", (210, 120, 60), hp=20, attack=6, defense=3, xp=50,
                    ai="hostile"),
    "troll": EnemyDef("Трол", "T", (60, 200, 170), hp=35, attack=8, defense=4, xp=100,
                      ai="hostile", regen=1),
    "boss": EnemyDef("Кралят на подземието", "K", (255, 200, 40), hp=80, attack=10,
                     defense=5, xp=500, ai="boss"),
}
BOSS_KEY = "boss"
BOSS_SUMMON_KEY = "goblin"     # кого призовава босът във втората фаза
BOSS_SUMMON_COUNT = 2
BOSS_PHASE_TWO_RATIO = 0.5     # под 50% HP → втора фаза
BOSS_ENRAGE_ATTACK = 2         # бонус атака във втората фаза

RANGED_MIN_DISTANCE = 3        # стрелецът държи дистанция 3–5
RANGED_MAX_DISTANCE = 5

# Тегла за спаунване: {име: {от_етаж: тегло}} – важи последният праг ≤ текущия етаж.
ENEMY_SPAWN_WEIGHTS: dict[str, dict[int, int]] = {
    "rat": {1: 60, 4: 20, 7: 5},
    "goblin": {1: 35, 3: 45, 6: 30, 8: 20},
    "skeleton_archer": {3: 20, 6: 25},
    "orc": {4: 20, 6: 35, 8: 40},
    "troll": {7: 15, 9: 30},
}
# Максимален брой врагове на етаж: {от_етаж: брой}.
MAX_ENEMIES_BY_FLOOR: dict[int, int] = {1: 5, 3: 7, 5: 9, 7: 11, 9: 13, 10: 4}


# ---------------------------------------------------------------------------
# Предмети
# ---------------------------------------------------------------------------
INVENTORY_CAPACITY = 20
LIGHTNING_RANGE = FOV_RADIUS
CONFUSION_TURNS = 5


@dataclass(frozen=True)
class ItemDef:
    """Описание на тип предмет.

    kind: "heal", "lightning", "confusion", "weapon" или "armor".
    power: количество лечение / щета / ходове объркване / бонус от екипировката.
    """

    name: str
    char: str
    color: Color
    kind: str
    power: int


ITEMS: dict[str, ItemDef] = {
    "small_potion": ItemDef("Малка лечебна отвара", "!", (230, 90, 170), "heal", 10),
    "large_potion": ItemDef("Голяма лечебна отвара", "!", (255, 60, 110), "heal", 25),
    "lightning_scroll": ItemDef("Свитък на мълнията", "?", (255, 255, 110), "lightning", 20),
    "confusion_scroll": ItemDef("Свитък на объркването", "?", (190, 130, 255), "confusion",
                                CONFUSION_TURNS),
    "dagger": ItemDef("Кама", "/", (170, 210, 230), "weapon", 1),
    "sword": ItemDef("Меч", "/", (120, 190, 255), "weapon", 3),
    "axe": ItemDef("Брадва", "/", (90, 140, 255), "weapon", 5),
    "leather_armor": ItemDef("Кожена броня", "[", (180, 130, 80), "armor", 1),
    "chain_mail": ItemDef("Ризница", "[", (180, 180, 200), "armor", 3),
    "plate_armor": ItemDef("Плочеста броня", "[", (230, 230, 255), "armor", 5),
}

ITEM_SPAWN_WEIGHTS: dict[str, dict[int, int]] = {
    "small_potion": {1: 35, 5: 25},
    "large_potion": {3: 10, 5: 25},
    "lightning_scroll": {2: 12, 5: 18},
    "confusion_scroll": {2: 10, 5: 14},
    "dagger": {1: 10, 4: 3},
    "sword": {3: 8, 6: 5},
    "axe": {6: 6},
    "leather_armor": {1: 10, 4: 3},
    "chain_mail": {3: 8, 6: 5},
    "plate_armor": {6: 6},
}
MAX_ITEMS_BY_FLOOR: dict[int, int] = {1: 4, 4: 5, 7: 6}


# ---------------------------------------------------------------------------
# Рекорди
# ---------------------------------------------------------------------------
HIGHSCORE_PATH = Path(__file__).resolve().parent / "data" / "highscores.json"
HIGHSCORE_LIMIT = 10
HIGHSCORE_COLUMNS_X: tuple[int, ...] = (240, 340, 440, 530, 620, 720, 830, 960)
SCORE_PER_FLOOR = 100
SCORE_PER_KILL = 10
SCORE_PER_LEVEL = 50
SCORE_VICTORY_BONUS = 1000

"""Общи части за всички генератори на подземия."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from world import connectivity, tile
from world.tile import TileType

Point = tuple[int, int]
TileGrid = list[list[TileType]]


@dataclass(frozen=True)
class Rect:
    """Правоъгълник от подови клетки: колони x..x+w-1, редове y..y+h-1."""

    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        """Първата колона ВДЯСНО от правоъгълника (изключително)."""
        return self.x + self.w

    @property
    def y2(self) -> int:
        """Първият ред ПОД правоъгълника (изключително)."""
        return self.y + self.h

    @property
    def center(self) -> Point:
        """Централната клетка."""
        return self.x + self.w // 2, self.y + self.h // 2

    def contains(self, px: int, py: int) -> bool:
        """Дали клетката (px, py) е вътре."""
        return self.x <= px < self.x2 and self.y <= py < self.y2

    def intersects(self, other: Rect) -> bool:
        """Дали двата правоъгълника имат обща клетка."""
        return self.x < other.x2 and other.x < self.x2 and self.y < other.y2 and other.y < self.y2

    def cells(self) -> list[Point]:
        """Всички клетки на правоъгълника."""
        return [(cx, cy) for cx in range(self.x, self.x2) for cy in range(self.y, self.y2)]


@dataclass
class GenerationResult:
    """Резултат от генерирането на един етаж.

    Attributes:
        tiles: 2D масив [x][y] от типове тайлове.
        rooms: Стаите (празен списък за пещери).
        player_start: Началната позиция на играча.
        stairs: Позицията на стълбите надолу (None на последния етаж).
        start_area: Клетки около старта, където не се появяват врагове.
    """

    tiles: TileGrid
    rooms: list[Rect]
    player_start: Point
    stairs: Point | None
    start_area: set[Point] = field(default_factory=set)

    @property
    def width(self) -> int:
        """Ширина на картата."""
        return len(self.tiles)

    @property
    def height(self) -> int:
        """Височина на картата."""
        return len(self.tiles[0])

    def walkable_grid(self) -> list[list[bool]]:
        """2D масив [x][y] с проходимостта."""
        return [[t.walkable for t in column] for column in self.tiles]


class DungeonGenerator(ABC):
    """Абстрактен генератор (шаблонен метод).

    `generate()` описва общия алгоритъм: издълбай карта → избери старт → сложи стълби →
    провери свързаността. Наследниците имплементират само специфичните стъпки.
    """

    def __init__(self, width: int, height: int, rng: random.Random,
                 place_stairs: bool = True) -> None:
        self.width = width
        self.height = height
        self.rng = rng
        self.place_stairs = place_stairs

    def generate(self) -> GenerationResult:
        """Генерира етаж и проверява, че стълбите са достижими от старта."""
        tiles, rooms = self._carve()
        start = self._choose_start(tiles, rooms)
        stairs = self._choose_stairs(tiles, rooms, start) if self.place_stairs else None
        if stairs is not None:
            tiles[stairs[0]][stairs[1]] = tile.STAIRS_DOWN
        result = GenerationResult(tiles, rooms, start, stairs, self._start_area(start, rooms))
        grid = result.walkable_grid()
        targets = [stairs] if stairs is not None else []
        if not connectivity.all_reachable(grid, start, targets):
            raise RuntimeError("Генерираната карта не е свързана")  # не трябва да се случва
        return result

    def new_grid(self, fill: TileType = tile.WALL) -> TileGrid:
        """Нова карта, запълнена с `fill`."""
        return [[fill] * self.height for _ in range(self.width)]

    @abstractmethod
    def _carve(self) -> tuple[TileGrid, list[Rect]]:
        """Издълбава подовете. Връща тайловете и списъка стаи."""

    @abstractmethod
    def _choose_start(self, tiles: TileGrid, rooms: list[Rect]) -> Point:
        """Избира началната позиция на играча."""

    @abstractmethod
    def _start_area(self, start: Point, rooms: list[Rect]) -> set[Point]:
        """Зоната около старта, в която няма да се появяват врагове."""

    def _choose_stairs(self, tiles: TileGrid, rooms: list[Rect], start: Point) -> Point:
        """По подразбиране: най-далечната достижима клетка от старта."""
        grid = [[t.walkable for t in column] for column in tiles]
        return connectivity.farthest_point(grid, start)

"""BSP (Binary Space Partitioning) генератор на подземия със стаи и коридори.

Идея:
1. Правоъгълникът на картата се дели рекурсивно на две, докато частите станат малки.
   Получава се двоично дърво; листата са непресичащи се правоъгълници.
2. Във всяко листо се издълбава стая – така стаите НИКОГА не се застъпват.
3. За всеки вътрешен възел се свързва стая от лявото поддърво със стая от дясното.
   Понеже всеки възел свързва двете си половини, по индукция цялото дърво е свързано.
"""

from __future__ import annotations

from dataclasses import dataclass

import config
from world import connectivity, tile
from world.generators.base import DungeonGenerator, Point, Rect, TileGrid


@dataclass
class BSPNode:
    """Възел от BSP дървото.

    Attributes:
        rect: Областта, която възелът покрива.
        left: Лявото/горното дете (None за листо).
        right: Дясното/долното дете (None за листо).
        room: Стаята в листото (само за листа).
    """

    rect: Rect
    left: BSPNode | None = None
    right: BSPNode | None = None
    room: Rect | None = None

    @property
    def is_leaf(self) -> bool:
        """Дали възелът е листо."""
        return self.left is None and self.right is None

    def rooms(self) -> list[Rect]:
        """Всички стаи в поддървото (обхождане отляво надясно)."""
        if self.is_leaf:
            return [self.room] if self.room is not None else []
        assert self.left is not None and self.right is not None
        return self.left.rooms() + self.right.rooms()


class BSPGenerator(DungeonGenerator):
    """Генератор на подземие със стаи и L-образни коридори."""

    def _carve(self) -> tuple[TileGrid, list[Rect]]:
        """Строи дървото, издълбава стаите и коридорите."""
        tiles = self.new_grid(tile.WALL)
        root = BSPNode(Rect(0, 0, self.width, self.height))
        self._split(root, depth=0)
        self._create_rooms(root, tiles)
        self._connect(root, tiles)
        return tiles, root.rooms()

    # ------------------------------------------------------------------ деление
    def _choose_vertical(self, rect: Rect, depth: int) -> bool:
        """Дали да режем вертикално (по x). Режем по-дългата страна, ако е много по-дълга."""
        if rect.w / rect.h > config.BSP_ASPECT_RATIO:
            return True
        if rect.h / rect.w > config.BSP_ASPECT_RATIO:
            return False
        return depth % 2 == 0  # иначе редуваме посоките

    def _split(self, node: BSPNode, depth: int) -> None:
        """Рекурсивно дели възела, докато частите станат твърде малки."""
        if depth >= config.BSP_MAX_DEPTH:
            return
        rect = node.rect
        vertical = self._choose_vertical(rect, depth)
        min_leaf = config.BSP_MIN_LEAF_SIZE
        length = rect.w if vertical else rect.h
        if length < 2 * min_leaf:
            # Не може да се дели в избраната посока – пробваме другата.
            vertical = not vertical
            length = rect.w if vertical else rect.h
            if length < 2 * min_leaf:
                return  # листо
        ratio = self.rng.uniform(config.BSP_SPLIT_MIN, config.BSP_SPLIT_MAX)
        cut = max(min_leaf, min(length - min_leaf, int(length * ratio)))
        if vertical:
            node.left = BSPNode(Rect(rect.x, rect.y, cut, rect.h))
            node.right = BSPNode(Rect(rect.x + cut, rect.y, rect.w - cut, rect.h))
        else:
            node.left = BSPNode(Rect(rect.x, rect.y, rect.w, cut))
            node.right = BSPNode(Rect(rect.x, rect.y + cut, rect.w, rect.h - cut))
        self._split(node.left, depth + 1)
        self._split(node.right, depth + 1)

    # ------------------------------------------------------------------ стаи
    def _random_room(self, leaf: Rect) -> Rect:
        """Стая с произволен размер вътре в листото, с отстъп от ръбовете му."""
        margin = config.BSP_ROOM_MARGIN
        max_w = min(config.BSP_ROOM_MAX_SIZE, leaf.w - 2 * margin)
        max_h = min(config.BSP_ROOM_MAX_SIZE, leaf.h - 2 * margin)
        w = self.rng.randint(config.BSP_ROOM_MIN_SIZE, max_w)
        h = self.rng.randint(config.BSP_ROOM_MIN_SIZE, max_h)
        x = self.rng.randint(leaf.x + margin, leaf.x2 - margin - w)
        y = self.rng.randint(leaf.y + margin, leaf.y2 - margin - h)
        return Rect(x, y, w, h)

    def _create_rooms(self, node: BSPNode, tiles: TileGrid) -> None:
        """Слага по една стая във всяко листо."""
        if node.is_leaf:
            node.room = self._random_room(node.rect)
            carve_rect(tiles, node.room)
            return
        assert node.left is not None and node.right is not None
        self._create_rooms(node.left, tiles)
        self._create_rooms(node.right, tiles)

    # ------------------------------------------------------------------ коридори
    def _connect(self, node: BSPNode, tiles: TileGrid) -> None:
        """Свързва двете половини на всеки вътрешен възел (отдолу нагоре)."""
        if node.is_leaf:
            return
        assert node.left is not None and node.right is not None
        self._connect(node.left, tiles)
        self._connect(node.right, tiles)
        # От всички двойки избираме най-близките стаи – коридорите стават по-къси.
        room_a, room_b = min(
            ((a, b) for a in node.left.rooms() for b in node.right.rooms()),
            key=lambda pair: _distance2(pair[0].center, pair[1].center),
        )
        self._carve_l_corridor(tiles, room_a.center, room_b.center)

    def _carve_l_corridor(self, tiles: TileGrid, start: Point, end: Point) -> None:
        """L-образен коридор: първо хоризонтално или първо вертикално (случайно)."""
        (x1, y1), (x2, y2) = start, end
        if self.rng.random() < 0.5:
            corner = (x2, y1)
        else:
            corner = (x1, y2)
        carve_line(tiles, start, corner)
        carve_line(tiles, corner, end)

    # ------------------------------------------------------------------ старт/стълби
    def _choose_start(self, tiles: TileGrid, rooms: list[Rect]) -> Point:
        """Играчът започва в центъра на първата стая."""
        return rooms[0].center

    def _choose_stairs(self, tiles: TileGrid, rooms: list[Rect], start: Point) -> Point:
        """Стълбите са в центъра на стаята, най-далечна (по път) от старта."""
        grid = [[t.walkable for t in column] for column in tiles]
        distances = connectivity.bfs_distances(grid, start)
        return max((room.center for room in rooms), key=lambda c: distances.get(c, -1))

    def _start_area(self, start: Point, rooms: list[Rect]) -> set[Point]:
        """Стартовата стая е безопасна зона."""
        for room in rooms:
            if room.contains(*start):
                return set(room.cells())
        return {start}


def carve_rect(tiles: TileGrid, rect: Rect) -> None:
    """Прави всички клетки на правоъгълника под."""
    for x, y in rect.cells():
        tiles[x][y] = tile.FLOOR


def carve_line(tiles: TileGrid, start: Point, end: Point) -> None:
    """Прави под по права хоризонтална или вертикална линия (включително краищата)."""
    (x1, y1), (x2, y2) = start, end
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            tiles[x][y] = tile.FLOOR


def _distance2(a: Point, b: Point) -> int:
    """Квадрат на Евклидовото разстояние (без корен – достатъчно за сравнение)."""
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

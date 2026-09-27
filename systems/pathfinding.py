"""A* търсене на път в мрежа с 8-посочно движение.

- Всяка стъпка (и диагонална) струва 1, затова евристиката е Chebyshev разстоянието
  max(|dx|, |dy|) – точно минималният брой стъпки без препятствия. Тя никога не
  надценява (admissible), следователно A* намира най-кратък път.
- Клетки, заети от други същества, НЕ са непроходими, а имат висока цена. Така враг
  заобикаля другарите си, ако има обход, но не "замръзва", ако няма (напр. в коридор).
- Приоритетната опашка е `heapq` (двоична купчина) → O(E log V).
"""

from __future__ import annotations

import heapq
import itertools
from collections.abc import Collection, Iterator

import config

Grid = list[list[bool]]
Point = tuple[int, int]

DIRECTIONS_8: tuple[Point, ...] = (
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
)


def chebyshev(a: Point, b: Point) -> int:
    """Chebyshev разстояние – брой ходове между a и b при 8-посочно движение."""
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def find_path(
    walkable: Grid,
    start: Point,
    goal: Point,
    occupied: Collection[Point] = (),
    occupied_cost: int = config.PATH_OCCUPIED_COST,
) -> list[Point] | None:
    """Намира най-евтиния път от `start` до `goal`.

    Args:
        walkable: 2D масив [x][y] – проходими ли са клетките.
        start: Начална клетка.
        goal: Целева клетка.
        occupied: Клетки, заети от същества (допълнителна цена).
        occupied_cost: Допълнителната цена за заета клетка.

    Returns:
        Списък от клетки БЕЗ `start` и С `goal` ([] ако start == goal),
        или None, ако целта е недостижима.
    """
    width, height = len(walkable), len(walkable[0])
    if start == goal:
        return []
    if not (0 <= goal[0] < width and 0 <= goal[1] < height) or not walkable[goal[0]][goal[1]]:
        return None

    counter = itertools.count()  # разрешава равенства в купчината без сравнение на точки
    open_heap: list[tuple[int, int, Point]] = [(chebyshev(start, goal), next(counter), start)]
    g_cost: dict[Point, int] = {start: 0}
    came_from: dict[Point, Point] = {}
    closed: set[Point] = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current == goal:
            return _reconstruct(came_from, current)
        if current in closed:
            continue  # остарял запис (намерили сме по-евтин път по-рано)
        closed.add(current)
        for nxt in walkable_neighbors(walkable, current):
            if nxt in closed:
                continue
            step = 1 + (occupied_cost if nxt in occupied and nxt != goal else 0)
            new_g = g_cost[current] + step
            if new_g < g_cost.get(nxt, new_g + 1):
                g_cost[nxt] = new_g
                came_from[nxt] = current
                heapq.heappush(open_heap, (new_g + chebyshev(nxt, goal), next(counter), nxt))
    return None


def walkable_neighbors(walkable: Grid, point: Point) -> Iterator[Point]:
    """Проходимите съседи (8 посоки) на клетката в границите на картата."""
    width, height = len(walkable), len(walkable[0])
    for dx, dy in DIRECTIONS_8:
        x, y = point[0] + dx, point[1] + dy
        if 0 <= x < width and 0 <= y < height and walkable[x][y]:
            yield x, y


def _reconstruct(came_from: dict[Point, Point], current: Point) -> list[Point]:
    """Възстановява пътя, вървейки назад по `came_from`."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.pop()  # махаме началната клетка
    path.reverse()
    return path

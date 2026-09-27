"""Свързаност на картата: BFS, flood fill и свързани региони.

Работим с 4-посочна свързаност (горе/долу/ляво/дясно). Тя е по-строга от 8-посочната:
ако две клетки са свързани 4-посочно, те със сигурност са достижими и при 8-посочно
движение. Така гаранцията за свързаност не зависи от диагонали между два ъгъла на стени.

Всички функции приемат `passable[x][y]` – 2D масив от bool.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

Grid = list[list[bool]]
Point = tuple[int, int]

NEIGHBORS_4: tuple[Point, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def bfs_distances(passable: Grid, start: Point) -> dict[Point, int]:
    """Разстояние (брой стъпки) от `start` до всяка достижима клетка.

    Сложност: O(W*H) – всяка клетка влиза в опашката най-много веднъж.
    """
    width, height = len(passable), len(passable[0])
    sx, sy = start
    if not passable[sx][sy]:
        return {}
    distances = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in NEIGHBORS_4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and passable[nx][ny] \
                    and (nx, ny) not in distances:
                distances[(nx, ny)] = distances[(x, y)] + 1
                queue.append((nx, ny))
    return distances


def flood_fill(passable: Grid, start: Point) -> set[Point]:
    """Множеството клетки, достижими от `start`."""
    return set(bfs_distances(passable, start))


def find_regions(passable: Grid) -> list[set[Point]]:
    """Всички свързани региони от проходими клетки, от най-голям към най-малък."""
    width, height = len(passable), len(passable[0])
    seen: set[Point] = set()
    regions: list[set[Point]] = []
    for x in range(width):
        for y in range(height):
            if passable[x][y] and (x, y) not in seen:
                region = flood_fill(passable, (x, y))
                seen |= region
                regions.append(region)
    regions.sort(key=len, reverse=True)
    return regions


def all_reachable(passable: Grid, start: Point, targets: Iterable[Point]) -> bool:
    """True, ако всички `targets` са достижими от `start`."""
    reachable = flood_fill(passable, start)
    return all(target in reachable for target in targets)


def farthest_point(passable: Grid, start: Point) -> Point:
    """Най-далечната достижима клетка от `start` (по брой стъпки)."""
    distances = bfs_distances(passable, start)
    return max(distances, key=lambda p: (distances[p], p))

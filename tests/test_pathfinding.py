"""Тестове за A* (Етап 5)."""

from __future__ import annotations

from collections import deque

import pytest

from systems.pathfinding import DIRECTIONS_8, chebyshev, find_path


def grid_from(rows: list[str]) -> list[list[bool]]:
    """'#' = стена, всичко друго = проходимо."""
    return [[rows[y][x] != "#" for y in range(len(rows))] for x in range(len(rows[0]))]


def bfs_length(grid: list[list[bool]], start: tuple[int, int], goal: tuple[int, int]) -> int:
    """Референтна дължина на най-краткия път (8 посоки) чрез BFS."""
    width, height = len(grid), len(grid[0])
    dist = {start: 0}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        for dx, dy in DIRECTIONS_8:
            nxt = (cur[0] + dx, cur[1] + dy)
            if 0 <= nxt[0] < width and 0 <= nxt[1] < height and grid[nxt[0]][nxt[1]] \
                    and nxt not in dist:
                dist[nxt] = dist[cur] + 1
                queue.append(nxt)
    return dist[goal]


def assert_valid_path(grid: list[list[bool]], start: tuple[int, int],
                      path: list[tuple[int, int]]) -> None:
    """Всяка стъпка е към съседна проходима клетка."""
    prev = start
    for step in path:
        assert chebyshev(prev, step) == 1
        assert grid[step[0]][step[1]]
        prev = step


def test_straight_path_on_open_grid() -> None:
    grid = grid_from(["......", "......", "......"])
    path = find_path(grid, (0, 0), (5, 0))
    assert path is not None
    assert len(path) == 5
    assert path[-1] == (5, 0)


def test_diagonal_moves_are_used() -> None:
    grid = grid_from(["....."] * 5)
    path = find_path(grid, (0, 0), (4, 4))
    assert path is not None and len(path) == 4  # 4 диагонални стъпки


MAZE = [
    "..........",
    ".########.",
    ".#......#.",
    ".#.####.#.",
    ".#.#..#.#.",
    ".#.#.##.#.",
    "...#......",
]


def test_finds_shortest_path_around_walls() -> None:
    grid = grid_from(MAZE)
    start, goal = (0, 0), (4, 4)
    path = find_path(grid, start, goal)
    assert path is not None
    assert path[-1] == goal
    assert_valid_path(grid, start, path)
    assert len(path) == bfs_length(grid, start, goal)


@pytest.mark.parametrize("goal", [(9, 6), (6, 2), (2, 6), (5, 4)])
def test_path_length_matches_bfs(goal: tuple[int, int]) -> None:
    grid = grid_from(MAZE)
    path = find_path(grid, (0, 0), goal)
    assert path is not None
    assert len(path) == bfs_length(grid, (0, 0), goal)


def test_unreachable_goal_returns_none() -> None:
    grid = grid_from([
        ".....",
        ".###.",
        ".#.#.",
        ".###.",
        ".....",
    ])
    assert find_path(grid, (0, 0), (2, 2)) is None


def test_goal_in_wall_returns_none() -> None:
    grid = grid_from(["..#.."])
    assert find_path(grid, (0, 0), (2, 0)) is None


def test_start_equals_goal() -> None:
    assert find_path(grid_from(["..."]), (1, 0), (1, 0)) == []


def test_occupied_cells_are_avoided_when_detour_exists() -> None:
    grid = grid_from(["....."] * 3)
    path = find_path(grid, (0, 1), (4, 1), occupied={(2, 1)})
    assert path is not None
    assert (2, 1) not in path
    assert len(path) == 4  # заобикалянето по диагонал не удължава пътя


def test_occupied_cells_are_not_impassable() -> None:
    # Коридор с ширина 1: единственият път минава през "заетата" клетка.
    grid = grid_from(["....."])
    path = find_path(grid, (0, 0), (4, 0), occupied={(2, 0)})
    assert path == [(1, 0), (2, 0), (3, 0), (4, 0)]

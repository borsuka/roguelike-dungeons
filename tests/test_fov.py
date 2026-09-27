"""Тестове за FOV (shadowcasting) и линия на видимост (Етап 4)."""

from __future__ import annotations

import pytest

import config
from engine.actions import MoveAction
from engine.world import World
from tests.helpers import grid_from
from world.fov import bresenham_line, compute_fov, has_line_of_sight


def open_grid(width: int, height: int) -> list[list[bool]]:
    """Изцяло прозрачна карта."""
    return [[True] * height for _ in range(width)]


def test_origin_is_always_visible() -> None:
    walls_everywhere = [[False] * 5 for _ in range(5)]
    assert (2, 2) in compute_fov(walls_everywhere, (2, 2), 8)


def test_wall_blocks_vision() -> None:
    rows = [
        "...........",
        "...........",
        ".....#.....",
        "...........",
        "...........",
    ]
    visible = compute_fov(grid_from(rows), (5, 4), 8)
    assert (5, 2) in visible       # самата стена се вижда
    assert (5, 1) not in visible   # клетката точно зад нея – не
    assert (5, 0) not in visible


def test_closed_room_hides_outside() -> None:
    rows = [
        ".........",
        ".#######.",
        ".#.....#.",
        ".#.....#.",
        ".#######.",
        ".........",
    ]
    visible = compute_fov(grid_from(rows), (4, 2), 8)
    assert (1, 1) in visible       # стените на стаята се виждат
    assert (0, 0) not in visible   # отвън – не
    assert (4, 5) not in visible


@pytest.mark.parametrize("radius", [1, 3, 8])
def test_radius_is_respected(radius: int) -> None:
    origin = (15, 15)
    visible = compute_fov(open_grid(31, 31), origin, radius)
    for x, y in visible:
        assert (x - origin[0]) ** 2 + (y - origin[1]) ** 2 <= radius ** 2
    # На открито поле всичко в радиуса трябва да се вижда.
    expected = {
        (x, y) for x in range(31) for y in range(31)
        if (x - 15) ** 2 + (y - 15) ** 2 <= radius ** 2
    }
    assert visible == expected


def test_fov_is_symmetric_on_open_field() -> None:
    visible = compute_fov(open_grid(21, 21), (10, 10), 6)
    for x, y in visible:
        assert (20 - x, y) in visible
        assert (x, 20 - y) in visible
        assert (y, x) in visible


def test_fov_near_map_edge_does_not_crash() -> None:
    visible = compute_fov(open_grid(5, 5), (0, 0), 8)
    assert (4, 4) in visible
    assert all(0 <= x < 5 and 0 <= y < 5 for x, y in visible)


def test_bresenham_line_endpoints_and_length() -> None:
    line = bresenham_line((0, 0), (5, 2))
    assert line[0] == (0, 0) and line[-1] == (5, 2)
    assert len(line) == 6  # Chebyshev разстояние + 1


def test_line_of_sight() -> None:
    rows = [
        ".....",
        "..#..",
        ".....",
    ]
    grid = grid_from(rows)
    assert not has_line_of_sight(grid, (0, 1), (4, 1))
    assert has_line_of_sight(grid, (0, 0), (4, 0))


def test_world_updates_visible_and_explored() -> None:
    world = World.new_game(seed=8)
    game_map = world.game_map
    px, py = world.player.position
    assert game_map.visible[px][py] and game_map.explored[px][py]
    far = (px + config.FOV_RADIUS + 5, py)
    if game_map.in_bounds(*far):
        assert not game_map.visible[far[0]][far[1]]
    # След като играчът се премести, видяното преди остава "explored".
    before = {(x, y) for x in range(game_map.width) for y in range(game_map.height)
              if game_map.explored[x][y]}
    for dx, dy in config.MOVE_KEYS.values():
        if MoveAction(world.player, dx, dy).perform(world):
            break
    world.update_fov()
    after = {(x, y) for x in range(game_map.width) for y in range(game_map.height)
             if game_map.explored[x][y]}
    assert before <= after

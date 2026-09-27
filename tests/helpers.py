"""Общи помощни функции за тестовете."""

from __future__ import annotations

from engine.world import World
from entities.factories import create_player
from world import tile
from world.game_map import GameMap


def grid_from(rows: list[str]) -> list[list[bool]]:
    """Прави 2D масив [x][y] от редове текст: '#' = стена/непрозрачно, всичко друго – не."""
    return [[rows[y][x] != "#" for y in range(len(rows))] for x in range(len(rows[0]))]


def make_arena(width: int = 12, height: int = 9, player_pos: tuple[int, int] = (2, 4),
               seed: int = 5) -> World:
    """Свят с една празна стая (рамка от стени) и играч на `player_pos`."""
    game_map = GameMap(width, height, fill=tile.WALL)
    for x in range(1, width - 1):
        for y in range(1, height - 1):
            game_map.set_tile(x, y, tile.FLOOR)
    player = create_player(*player_pos)
    game_map.add_entity(player)
    world = World(game_map, player, seed=seed)
    world.update_fov()
    return world

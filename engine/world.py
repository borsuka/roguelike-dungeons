"""Логическото състояние на една игра (без pygame).

`World` събира всичко, което действията трябва да знаят: картата, играча и т.н.
Отделен е от `Game` (pygame цикъла), за да може цялата логика да се тества без прозорец.
"""

from __future__ import annotations

import config
from entities.entity import Entity, RenderOrder
from world import tile
from world.game_map import GameMap


def build_test_map(width: int, height: int) -> GameMap:
    """Статична тестова карта: една голяма стая с няколко колони.

    Използва се само в Етап 1, преди да има истински генератори.
    """
    game_map = GameMap(width, height, fill=tile.WALL)
    for x in range(1, width - 1):
        for y in range(1, height - 1):
            game_map.set_tile(x, y, tile.FLOOR)
    for x in range(6, width - 6, 6):
        for y in range(4, height - 3, 5):
            game_map.set_tile(x, y, tile.WALL)
    return game_map


class World:
    """Контейнер за състоянието на играта.

    Attributes:
        game_map: Картата на текущия етаж.
        player: Обектът на играча.
    """

    def __init__(self, game_map: GameMap, player: Entity) -> None:
        self.game_map = game_map
        self.player = player

    @classmethod
    def new_test_world(cls) -> World:
        """Създава свят със статичната тестова карта и играч в центъра."""
        game_map = build_test_map(config.VIEW_WIDTH_TILES, config.VIEW_HEIGHT_TILES)
        player = Entity(
            game_map.width // 2, game_map.height // 2 + 1, "@", config.COLOR_PLAYER,
            "Играч", blocks_movement=True, render_order=RenderOrder.ACTOR,
        )
        game_map.add_entity(player)
        return cls(game_map, player)

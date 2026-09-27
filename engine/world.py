"""Логическото състояние на една игра (без pygame).

`World` събира всичко, което действията трябва да знаят: картата, играча, етажа, seed-а.
Отделен е от `Game` (pygame цикъла), за да може цялата логика да се тества без прозорец.
"""

from __future__ import annotations

import random

import config
from entities.entity import Entity, RenderOrder
from systems import rng
from world.game_map import GameMap
from world.generators.base import DungeonGenerator
from world.generators.bsp import BSPGenerator
from world.generators.cellular import CellularGenerator


def make_generator(floor: int, map_rng: random.Random) -> DungeonGenerator:
    """Избира генератор според етажа: нечетни – BSP подземия, четни – пещери."""
    if floor % 2 == 1:
        return BSPGenerator(config.MAP_WIDTH, config.MAP_HEIGHT, map_rng)
    return CellularGenerator(config.MAP_WIDTH, config.MAP_HEIGHT, map_rng)


def generate_floor(seed: int, floor: int) -> GameMap:
    """Генерира картата на етаж `floor` детерминистично от `seed`.

    Args:
        seed: Основният seed на играта.
        floor: Номер на етажа (от 1).
    """
    map_rng = rng.make_rng(rng.derive_seed(seed, "map", floor))
    return GameMap.from_generation(make_generator(floor, map_rng).generate())


def create_player() -> Entity:
    """Създава обекта на играча."""
    return Entity(0, 0, "@", config.COLOR_PLAYER, "Играч",
                  blocks_movement=True, render_order=RenderOrder.ACTOR)


class World:
    """Контейнер за състоянието на играта.

    Attributes:
        game_map: Картата на текущия етаж.
        player: Обектът на играча.
        seed: Основният seed на играта.
        floor: Текущият етаж (от 1).
        rng: Генератор за бой, AI и т.н. (картите ползват собствени производни seed-ове).
    """

    def __init__(self, game_map: GameMap, player: Entity, seed: int = 0, floor: int = 1) -> None:
        self.game_map = game_map
        self.player = player
        self.seed = seed
        self.floor = floor
        self.rng = rng.make_rng(rng.derive_seed(seed, "gameplay"))

    @classmethod
    def new_game(cls, seed: int | None = None) -> World:
        """Нова игра на етаж 1.

        Args:
            seed: Seed на играта; None означава случаен.
        """
        if seed is None:
            seed = rng.new_seed()
        player = create_player()
        world = cls(generate_floor(seed, 1), player, seed=seed, floor=1)
        world._place_player()
        world.update_fov()
        return world

    def update_fov(self) -> None:
        """Преизчислява видимостта от позицията на играча."""
        self.game_map.update_fov(self.player.position, config.FOV_RADIUS)

    @property
    def player_on_stairs(self) -> bool:
        """Дали играчът стои на стълбите надолу."""
        return self.game_map.stairs == self.player.position

    def descend(self) -> None:
        """Слиза на следващия етаж: нова карта, играчът – на старта ѝ."""
        self.floor += 1
        self.game_map = generate_floor(self.seed, self.floor)
        self._place_player()
        self.update_fov()

    def _place_player(self) -> None:
        """Поставя играча на старта на текущата карта."""
        self.player.place(*self.game_map.player_start)
        self.game_map.add_entity(self.player)

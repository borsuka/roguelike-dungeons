"""Логическото състояние на една игра (без pygame).

`World` събира всичко, което действията трябва да знаят: картата, играча, лога,
етажа, seed-а и статистиката. Отделен е от `Game` (pygame цикъла), за да може цялата
логика да се тества без прозорец.
"""

from __future__ import annotations

import random

import config
from entities.actor import Actor
from entities.factories import create_player
from systems import rng
from ui.message_log import MessageLog
from world import spawner
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
    """Генерира и попълва етаж `floor` детерминистично от `seed`.

    Картата и съдържанието ползват отделни производни seed-ове, за да не зависи
    картата от броя случайни числа, изразходвани за враговете (и обратно).

    Args:
        seed: Основният seed на играта.
        floor: Номер на етажа (от 1).
    """
    map_rng = rng.make_rng(rng.derive_seed(seed, "map", floor))
    game_map = GameMap.from_generation(make_generator(floor, map_rng).generate())
    spawn_rng = rng.make_rng(rng.derive_seed(seed, "spawn", floor))
    spawner.populate(game_map, floor, spawn_rng)
    return game_map


class World:
    """Контейнер за състоянието на играта.

    Attributes:
        game_map: Картата на текущия етаж.
        player: Играчът.
        seed: Основният seed на играта.
        floor: Текущият етаж (от 1).
        rng: Генератор за бой, AI и т.н. (картите ползват собствени производни seed-ове).
        message_log: Логът на съобщенията.
        turn: Брой изиграни ходове.
        kills: Брой убити врагове.
    """

    def __init__(self, game_map: GameMap, player: Actor, seed: int = 0, floor: int = 1) -> None:
        self.game_map = game_map
        self.player = player
        self.seed = seed
        self.floor = floor
        self.rng = rng.make_rng(rng.derive_seed(seed, "gameplay"))
        self.message_log = MessageLog()
        self.turn = 0
        self.kills = 0

    @classmethod
    def new_game(cls, seed: int | None = None) -> World:
        """Нова игра на етаж 1.

        Args:
            seed: Seed на играта; None означава случаен.
        """
        if seed is None:
            seed = rng.new_seed()
        world = cls(generate_floor(seed, 1), create_player(), seed=seed, floor=1)
        world._place_player()
        world.update_fov()
        world.message_log.add("Добре дошъл в подземията! Слез до етаж "
                              f"{config.BOSS_FLOOR} и победи краля.", config.COLOR_MSG_WELCOME)
        return world

    # ------------------------------------------------------------------ състояние
    @property
    def game_over(self) -> bool:
        """Играчът е мъртъв."""
        return not self.player.is_alive

    @property
    def player_on_stairs(self) -> bool:
        """Дали играчът стои на стълбите надолу."""
        return self.game_map.stairs == self.player.position

    def visible_enemies(self) -> list[Actor]:
        """Живите врагове в зрителното поле на играча."""
        return [a for a in self.game_map.actors
                if a is not self.player and self.game_map.is_visible(a.x, a.y)]

    def update_fov(self) -> None:
        """Преизчислява видимостта от позицията на играча."""
        self.game_map.update_fov(self.player.position, config.FOV_RADIUS)

    # ------------------------------------------------------------------ събития
    def descend(self) -> None:
        """Слиза на следващия етаж: нова карта, играчът – на старта ѝ."""
        self.floor += 1
        self.game_map = generate_floor(self.seed, self.floor)
        self._place_player()
        self.update_fov()
        self.message_log.add(f"Слизаш на етаж {self.floor}.", config.COLOR_MSG_DESCEND)

    def handle_death(self, actor: Actor) -> None:
        """Обработва смърт: съобщение, статистика, превръщане в труп."""
        if actor is self.player:
            self.message_log.add("Ти загина!", config.COLOR_MSG_PLAYER_DIE)
            actor.become_corpse()
            return
        self.message_log.add(f"{actor.name} умира!", config.COLOR_MSG_ENEMY_DIE)
        self.kills += 1
        actor.become_corpse()

    def _place_player(self) -> None:
        """Поставя играча на старта на текущата карта."""
        self.player.place(*self.game_map.player_start)
        self.game_map.add_entity(self.player)

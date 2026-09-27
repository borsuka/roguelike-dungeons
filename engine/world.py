"""Логическото състояние на една игра (без pygame).

`World` събира всичко, което действията трябва да знаят: картата, играча, лога,
етажа, seed-а и статистиката. Отделен е от `Game` (pygame цикъла), за да може цялата
логика да се тества без прозорец.
"""

from __future__ import annotations

import random

import config
from entities.actor import Actor
from entities.factories import create_enemy, create_player
from systems import pathfinding, rng
from ui.message_log import MessageLog
from world import connectivity, fov, spawner
from world.game_map import GameMap
from world.generators.base import DungeonGenerator
from world.generators.bsp import BossArenaGenerator, BSPGenerator
from world.generators.cellular import CellularGenerator


def make_generator(floor: int, map_rng: random.Random) -> DungeonGenerator:
    """Избира генератор: етажът на боса – арена; нечетни – BSP; четни – пещери."""
    if floor >= config.BOSS_FLOOR:
        return BossArenaGenerator(config.MAP_WIDTH, config.MAP_HEIGHT, map_rng)
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
    verify_floor(game_map)
    return game_map


def verify_floor(game_map: GameMap) -> None:
    """Задължителна проверка: стълбите и всички предмети са достижими от старта.

    Raises:
        RuntimeError: Ако нещо е недостижимо (това би било грешка в генератора).
    """
    targets = [item.position for item in game_map.items]
    if game_map.stairs is not None:
        targets.append(game_map.stairs)
    if not connectivity.all_reachable(game_map.walkable_grid(), game_map.player_start, targets):
        raise RuntimeError("Недостижими стълби или предмети на етажа")


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
        max_floor: Най-дълбокият достигнат етаж.
        victory: True, след като босът е победен.
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
        self.max_floor = floor
        self.victory = False

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

    def clear_shot(self, start: tuple[int, int], end: tuple[int, int]) -> bool:
        """Има ли права линия без стени и без други същества между start и end."""
        game_map = self.game_map
        if not fov.has_line_of_sight(game_map.transparent_grid(), start, end):
            return False
        between = fov.bresenham_line(start, end)[1:-1]
        return all(game_map.get_blocking_entity_at(x, y) is None for x, y in between)

    # ------------------------------------------------------------------ събития
    def descend(self) -> None:
        """Слиза на следващия етаж: нова карта, играчът – на старта ѝ."""
        self.floor += 1
        self.max_floor = max(self.max_floor, self.floor)
        self.game_map = generate_floor(self.seed, self.floor)
        self._place_player()
        self.update_fov()
        self.message_log.add(f"Слизаш на етаж {self.floor}.", config.COLOR_MSG_DESCEND)
        if self.floor >= config.BOSS_FLOOR:
            self.message_log.add("Усещаш присъствието на Краля на подземието...",
                                 config.COLOR_MSG_BOSS)

    def handle_death(self, actor: Actor) -> None:
        """Обработва смърт: съобщение, статистика, превръщане в труп."""
        if actor is self.player:
            self.message_log.add("Ти загина!", config.COLOR_MSG_PLAYER_DIE)
            actor.become_corpse()
            return
        self.message_log.add(f"{actor.name} умира!", config.COLOR_MSG_ENEMY_DIE)
        self.kills += 1
        is_boss = actor.kind == config.BOSS_KEY
        actor.become_corpse()
        self._reward_xp(actor.fighter.xp_reward)
        if is_boss:
            self.victory = True
            self.message_log.add("Кралят на подземието е победен! Ти спечели!",
                                 config.COLOR_VICTORY)

    def _reward_xp(self, xp: int) -> None:
        """Дава опит на играча и съобщава за ново ниво."""
        level = self.player.level
        if level is None or xp <= 0:
            return
        self.message_log.add(f"Получаваш {xp} опит.", config.COLOR_MSG_XP)
        if level.add_xp(xp):
            self.message_log.add(f"Достигаш ниво {level.current_level + 1}!",
                                 config.COLOR_MSG_LEVEL_UP)

    def summon_near(self, summoner: Actor, key: str, count: int) -> int:
        """Създава до `count` врагове в свободни клетки около `summoner`.

        Returns:
            Колко са създадени реално (може да няма място).
        """
        created = 0
        for dx, dy in pathfinding.DIRECTIONS_8:
            if created >= count:
                break
            x, y = summoner.x + dx, summoner.y + dy
            if self.game_map.is_free(x, y):
                self.game_map.add_entity(create_enemy(key, x, y))
                created += 1
        return created

    def _place_player(self) -> None:
        """Поставя играча на старта на текущата карта."""
        self.player.place(*self.game_map.player_start)
        self.game_map.add_entity(self.player)

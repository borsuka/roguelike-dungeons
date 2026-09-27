"""Разполагане на врагове (и по-късно предмети) на етажа според дълбочината."""

from __future__ import annotations

import random
from typing import TypeVar

import config
from entities.factories import create_enemy
from world.game_map import GameMap

T = TypeVar("T")
Point = tuple[int, int]


def value_for_floor(table: dict[int, T], floor: int) -> T:
    """Стойността от таблица {от_етаж: стойност} за дадения етаж.

    Пример: {1: 5, 4: 8} → етажи 1–3 дават 5, етаж 4 и нагоре – 8.
    """
    eligible = [start for start in table if start <= floor]
    if not eligible:
        raise ValueError(f"Няма стойност за етаж {floor}")
    return table[max(eligible)]


def weights_for_floor(weights: dict[str, dict[int, int]], floor: int) -> dict[str, int]:
    """Теглата на всички видове за етажа (видовете, които още не се появяват, отпадат)."""
    result = {}
    for key, table in weights.items():
        if any(start <= floor for start in table):
            weight = value_for_floor(table, floor)
            if weight > 0:
                result[key] = weight
    return result


def weighted_choice(weights: dict[str, int], rng: random.Random) -> str:
    """Претеглен случаен избор: вероятността е пропорционална на теглото."""
    keys = sorted(weights)  # сортираме за детерминизъм
    return rng.choices(keys, weights=[weights[k] for k in keys], k=1)[0]


def free_spawn_cells(game_map: GameMap) -> list[Point]:
    """Подови клетки, подходящи за враг: не в стартовата зона, не на стълбите, свободни."""
    cells = []
    for x in range(game_map.width):
        for y in range(game_map.height):
            if (x, y) in game_map.start_area or (x, y) == game_map.stairs:
                continue
            if game_map.is_free(x, y):
                cells.append((x, y))
    return cells


def spawn_enemies(game_map: GameMap, floor: int, rng: random.Random) -> int:
    """Поставя врагове на етажа. Връща колко са поставени."""
    maximum = value_for_floor(config.MAX_ENEMIES_BY_FLOOR, floor)
    count = rng.randint(maximum // 2, maximum)
    cells = free_spawn_cells(game_map)
    rng.shuffle(cells)
    weights = weights_for_floor(config.ENEMY_SPAWN_WEIGHTS, floor)
    placed = 0
    for x, y in cells[:count]:
        game_map.add_entity(create_enemy(weighted_choice(weights, rng), x, y))
        placed += 1
    return placed


def populate(game_map: GameMap, floor: int, rng: random.Random) -> None:
    """Попълва етажа със съдържание."""
    spawn_enemies(game_map, floor, rng)

"""Тестове за Cellular Automata генератора и смяната на етажи (Етап 3)."""

from __future__ import annotations

import functools

import pytest

import config
from engine.actions import DescendAction
from engine.world import World, generate_floor
from systems.rng import make_rng
from world import connectivity, tile
from world.generators.base import DungeonGenerator, GenerationResult
from world.generators.bsp import BSPGenerator
from world.generators.cellular import CellularGenerator

SEEDS = [0, 3, 11, 42, 500, 31337]


@functools.lru_cache(maxsize=None)
def generate(seed: int) -> GenerationResult:
    return CellularGenerator(config.MAP_WIDTH, config.MAP_HEIGHT, make_rng(seed)).generate()


@pytest.mark.parametrize("seed", SEEDS)
def test_border_is_always_wall(seed: int) -> None:
    result = generate(seed)
    w, h = result.width, result.height
    border = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] \
        + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    assert all(result.tiles[x][y] is tile.WALL for x, y in border)


@pytest.mark.parametrize("seed", SEEDS)
def test_only_one_region_remains(seed: int) -> None:
    result = generate(seed)
    assert len(connectivity.find_regions(result.walkable_grid())) == 1


@pytest.mark.parametrize("seed", SEEDS)
def test_minimum_floor_percentage(seed: int) -> None:
    result = generate(seed)
    floor_cells = sum(t.walkable for column in result.tiles for t in column)
    assert floor_cells >= config.CA_MIN_FLOOR_RATIO * result.width * result.height


@pytest.mark.parametrize("seed", SEEDS)
def test_start_and_stairs_are_valid(seed: int) -> None:
    result = generate(seed)
    assert result.stairs is not None
    assert result.tiles[result.stairs[0]][result.stairs[1]] is tile.STAIRS_DOWN
    assert result.tiles[result.player_start[0]][result.player_start[1]].walkable
    assert result.player_start in result.start_area
    assert connectivity.all_reachable(result.walkable_grid(), result.player_start,
                                      [result.stairs])


def test_same_seed_gives_same_cave() -> None:
    a, b = generate(777), generate(777)
    assert a.tiles == b.tiles
    assert a.player_start == b.player_start
    assert a.stairs == b.stairs


def test_count_walls_counts_outside_as_wall() -> None:
    gen = CellularGenerator(5, 5, make_rng(0))
    no_walls = [[False] * 5 for _ in range(5)]
    assert gen.count_walls(no_walls, 2, 2) == 0
    assert gen.count_walls(no_walls, 0, 0) == 5  # 5 от 9-те клетки са извън картата


def test_step_rule_threshold() -> None:
    gen = CellularGenerator(5, 5, make_rng(0))
    walls = [[False] * 5 for _ in range(5)]
    # 5 стени около центъра (2, 2) → центърът става стена
    for x, y in [(1, 1), (2, 1), (3, 1), (1, 2), (3, 2)]:
        walls[x][y] = True
    assert gen._step(walls, fill_empty=False)[2][2] is True
    walls[3][2] = False  # вече 4 стени → под
    assert gen._step(walls, fill_empty=False)[2][2] is False


def test_step_fills_empty_areas_in_early_iterations() -> None:
    gen = CellularGenerator(7, 7, make_rng(0))
    walls = [[False] * 7 for _ in range(7)]
    assert gen._step(walls, fill_empty=True)[3][3] is True
    assert gen._step(walls, fill_empty=False)[3][3] is False


def test_floor_types_alternate() -> None:
    # Нечетни етажи – BSP (има стаи), четни – пещери (няма стаи).
    assert generate_floor(5, 1).rooms
    assert not generate_floor(5, 2).rooms
    assert generate_floor(5, 3).rooms


def test_descend_only_on_stairs_and_generates_new_floor() -> None:
    world = World.new_game(seed=10)
    assert DescendAction(world.player).perform(world) is False
    assert world.floor == 1
    first_map = world.game_map
    world.player.place(*first_map.stairs)
    assert DescendAction(world.player).perform(world) is True
    assert world.floor == 2
    assert world.game_map is not first_map
    assert world.player.position == world.game_map.player_start
    assert world.player in world.game_map.entities


def test_generators_share_base_class() -> None:
    assert issubclass(BSPGenerator, DungeonGenerator)
    assert issubclass(CellularGenerator, DungeonGenerator)

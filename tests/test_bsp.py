"""Тестове за BSP генератора (Етап 2)."""

from __future__ import annotations

import itertools

import pytest

import config
from systems.rng import make_rng
from world import connectivity, tile
from world.generators.base import GenerationResult
from world.generators.bsp import BSPGenerator

SEEDS = [0, 1, 7, 42, 1234, 99999]


def generate(seed: int, width: int = config.MAP_WIDTH,
             height: int = config.MAP_HEIGHT) -> GenerationResult:
    return BSPGenerator(width, height, make_rng(seed)).generate()


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_are_inside_map_and_away_from_border(seed: int) -> None:
    result = generate(seed)
    assert result.rooms, "трябва да има поне една стая"
    for room in result.rooms:
        assert room.x >= 1 and room.y >= 1
        assert room.x2 <= result.width - 1 and room.y2 <= result.height - 1


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_do_not_overlap(seed: int) -> None:
    result = generate(seed)
    for a, b in itertools.combinations(result.rooms, 2):
        assert not a.intersects(b), f"{a} се застъпва с {b}"


@pytest.mark.parametrize("seed", SEEDS)
def test_rooms_respect_min_size(seed: int) -> None:
    for room in generate(seed).rooms:
        assert room.w >= config.BSP_ROOM_MIN_SIZE
        assert room.h >= config.BSP_ROOM_MIN_SIZE


@pytest.mark.parametrize("seed", SEEDS)
def test_all_floor_cells_are_connected(seed: int) -> None:
    result = generate(seed)
    regions = connectivity.find_regions(result.walkable_grid())
    assert len(regions) == 1


@pytest.mark.parametrize("seed", SEEDS)
def test_border_is_wall(seed: int) -> None:
    result = generate(seed)
    for x in range(result.width):
        assert result.tiles[x][0] is tile.WALL
        assert result.tiles[x][result.height - 1] is tile.WALL
    for y in range(result.height):
        assert result.tiles[0][y] is tile.WALL
        assert result.tiles[result.width - 1][y] is tile.WALL


@pytest.mark.parametrize("seed", SEEDS)
def test_stairs_exist_and_are_reachable(seed: int) -> None:
    result = generate(seed)
    assert result.stairs is not None
    sx, sy = result.stairs
    assert result.tiles[sx][sy] is tile.STAIRS_DOWN
    assert result.stairs != result.player_start
    assert connectivity.all_reachable(result.walkable_grid(), result.player_start,
                                      [result.stairs])


@pytest.mark.parametrize("seed", SEEDS)
def test_player_starts_on_floor_in_first_room(seed: int) -> None:
    result = generate(seed)
    px, py = result.player_start
    assert result.tiles[px][py].walkable
    assert result.rooms[0].contains(px, py)
    assert result.player_start in result.start_area


def test_same_seed_gives_same_map() -> None:
    a, b = generate(2024), generate(2024)
    assert a.tiles == b.tiles
    assert a.rooms == b.rooms
    assert a.stairs == b.stairs


def test_different_seeds_give_different_maps() -> None:
    assert generate(1).tiles != generate(2).tiles


def test_small_map_still_works() -> None:
    result = generate(3, width=24, height=12)
    assert len(result.rooms) >= 1
    assert len(connectivity.find_regions(result.walkable_grid())) == 1

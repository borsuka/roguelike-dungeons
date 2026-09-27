"""Тестове за движението на играча (Етап 1)."""

from __future__ import annotations

import pytest

import config
from engine.actions import MoveAction, WaitAction
from engine.world import World
from entities.entity import Entity
from world import tile
from world.game_map import GameMap


def make_world() -> World:
    """Свят 5x5: рамка от стени, под вътре, играч в центъра (2, 2)."""
    game_map = GameMap(5, 5, fill=tile.WALL)
    for x in range(1, 4):
        for y in range(1, 4):
            game_map.set_tile(x, y, tile.FLOOR)
    player = Entity(2, 2, "@", config.COLOR_PLAYER, "Играч", blocks_movement=True)
    game_map.add_entity(player)
    return World(game_map, player)


@pytest.mark.parametrize("dx, dy", [
    (0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1),
])
def test_player_moves_in_all_eight_directions(dx: int, dy: int) -> None:
    world = make_world()
    assert MoveAction(world.player, dx, dy).perform(world) is True
    assert world.player.position == (2 + dx, 2 + dy)


def test_player_cannot_walk_into_wall() -> None:
    world = make_world()
    world.player.place(1, 1)
    assert MoveAction(world.player, -1, 0).perform(world) is False
    assert MoveAction(world.player, 0, -1).perform(world) is False
    assert MoveAction(world.player, -1, -1).perform(world) is False
    assert world.player.position == (1, 1)


def test_player_cannot_walk_into_blocking_entity() -> None:
    world = make_world()
    blocker = Entity(3, 2, "X", config.COLOR_WHITE, "Пречка", blocks_movement=True)
    world.game_map.add_entity(blocker)
    assert MoveAction(world.player, 1, 0).perform(world) is False
    assert world.player.position == (2, 2)


def test_player_cannot_leave_map() -> None:
    world = make_world()
    world.game_map.set_tile(0, 2, tile.FLOOR)  # дупка в рамката
    world.player.place(0, 2)
    assert MoveAction(world.player, -1, 0).perform(world) is False


def test_wait_consumes_turn_without_moving() -> None:
    world = make_world()
    assert WaitAction(world.player).perform(world) is True
    assert world.player.position == (2, 2)


def test_static_test_world_has_walls_around() -> None:
    world = World.new_test_world()
    game_map = world.game_map
    assert not game_map.is_walkable(0, 0)
    assert game_map.is_walkable(*world.player.position)

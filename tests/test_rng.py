"""Тестове за централизирания random и детерминизма."""

from __future__ import annotations

import config
from engine.world import World, generate_floor
from systems.rng import derive_seed, make_rng, new_seed


def test_derive_seed_is_deterministic() -> None:
    assert derive_seed(42, "map", 3) == derive_seed(42, "map", 3)


def test_derive_seed_depends_on_every_part() -> None:
    base = derive_seed(42, "map", 3)
    assert derive_seed(43, "map", 3) != base
    assert derive_seed(42, "spawn", 3) != base
    assert derive_seed(42, "map", 4) != base


def test_derive_seed_is_in_range() -> None:
    for i in range(100):
        assert 0 <= derive_seed(i, "x") < config.SEED_MAX


def test_new_seed_is_in_range() -> None:
    assert 0 <= new_seed() < config.SEED_MAX


def test_make_rng_same_seed_same_sequence() -> None:
    a, b = make_rng(7), make_rng(7)
    assert [a.random() for _ in range(10)] == [b.random() for _ in range(10)]


def test_same_seed_gives_same_floor_with_same_content() -> None:
    a, b = generate_floor(99, 2), generate_floor(99, 2)
    assert a.tiles == b.tiles
    assert [(e.name, e.position) for e in a.entities] == [(e.name, e.position) for e in b.entities]


def test_new_game_with_same_seed_is_identical() -> None:
    a, b = World.new_game(seed=314), World.new_game(seed=314)
    assert a.player.position == b.player.position
    assert a.game_map.tiles == b.game_map.tiles


def test_floor_map_does_not_depend_on_gameplay_randomness() -> None:
    # Етаж 2 трябва да е същият, независимо колко random числа е изразходвал боят.
    world = World.new_game(seed=55)
    for _ in range(1000):
        world.rng.random()
    world.player.place(*world.game_map.stairs)
    world.descend()
    assert world.game_map.tiles == generate_floor(55, 2).tiles

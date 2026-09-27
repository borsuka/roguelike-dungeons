"""Тестове за спаунването по етажи и претегления избор."""

from __future__ import annotations

import collections
import random

import pytest

import config
from engine.world import generate_floor
from world.spawner import value_for_floor, weighted_choice, weights_for_floor


def test_value_for_floor_uses_last_threshold() -> None:
    table = {1: 5, 4: 8, 7: 12}
    assert [value_for_floor(table, f) for f in (1, 3, 4, 6, 7, 20)] == [5, 5, 8, 8, 12, 12]


def test_value_for_floor_without_threshold_raises() -> None:
    with pytest.raises(ValueError):
        value_for_floor({3: 1}, 1)


def test_zero_weight_removes_type() -> None:
    weights = weights_for_floor({"a": {1: 10, 5: 0}, "b": {1: 1}}, 6)
    assert weights == {"b": 1}


def test_weighted_choice_follows_weights() -> None:
    rng = random.Random(0)
    counts = collections.Counter(weighted_choice({"a": 90, "b": 10}, rng) for _ in range(5000))
    assert 0.85 < counts["a"] / 5000 < 0.95


@pytest.mark.parametrize("floor", [1, 3, 5, 7, 9])
def test_enemy_count_within_limits(floor: int) -> None:
    game_map = generate_floor(seed=11, floor=floor)
    enemies = [a for a in game_map.actors]
    maximum = value_for_floor(config.MAX_ENEMIES_BY_FLOOR, floor)
    assert maximum // 2 <= len(enemies) <= maximum


def test_enemies_never_in_start_area_and_items_never_stacked() -> None:
    for floor in range(1, config.BOSS_FLOOR):
        game_map = generate_floor(seed=321, floor=floor)
        for enemy in game_map.actors:
            assert enemy.position not in game_map.start_area
            assert enemy.position != game_map.stairs
        positions = [item.position for item in game_map.items]
        assert len(positions) == len(set(positions))


def test_only_allowed_enemies_on_first_floor() -> None:
    kinds = set()
    for seed in range(10):
        kinds |= {a.kind for a in generate_floor(seed, 1).actors}
    assert kinds <= {"rat", "goblin"}

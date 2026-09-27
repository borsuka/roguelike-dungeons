"""Тестове за бойната система, Fighter, AI и редуването на ходове (Етап 5)."""

from __future__ import annotations

import random

import pytest

import config
from components.ai import HostileAI
from components.fighter import Fighter
from engine.actions import BumpAction, MeleeAction, MoveAction, WaitAction
from engine.turn_manager import TurnManager
from engine.world import World
from entities.factories import create_enemy
from systems.combat import resolve_attack, roll_damage
from tests.helpers import make_arena
from world import tile


# ---------------------------------------------------------------------------
# Формула
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("attack, defense", [(1, 0), (1, 10), (0, 0), (3, 3), (2, 50), (10, 5)])
def test_damage_is_never_below_one(attack: int, defense: int) -> None:
    rng = random.Random(0)
    for _ in range(500):
        damage, _ = roll_damage(attack, defense, rng)
        assert damage >= 1


def test_damage_is_attack_minus_defense_plus_minus_variance() -> None:
    rng = random.Random(1)
    seen = set()
    for _ in range(2000):
        damage, critical = roll_damage(10, 4, rng)
        base = damage // config.CRIT_MULTIPLIER if critical else damage
        assert 6 - config.DAMAGE_VARIANCE <= base <= 6 + config.DAMAGE_VARIANCE
        seen.add(base)
    assert seen == {5, 6, 7}


def test_critical_hits_happen_about_five_percent() -> None:
    rng = random.Random(2)
    crits = sum(roll_damage(5, 0, rng)[1] for _ in range(10000))
    assert 0.03 < crits / 10000 < 0.07


def test_missed_attack_has_zero_damage() -> None:
    rng = random.Random(3)
    results = [resolve_attack(5, 0, rng) for _ in range(2000)]
    misses = [r for r in results if r.missed]
    assert misses and all(r.damage == 0 for r in misses)
    assert all(r.damage >= 1 for r in results if not r.missed)


# ---------------------------------------------------------------------------
# Fighter
# ---------------------------------------------------------------------------
def test_take_damage_and_death() -> None:
    fighter = Fighter(hp=10, attack=1, defense=0)
    assert fighter.take_damage(4) == 4
    assert fighter.hp == 6
    assert fighter.take_damage(100) == 6
    assert fighter.hp == 0 and fighter.is_dead


def test_heal_does_not_exceed_max() -> None:
    fighter = Fighter(hp=10, attack=1, defense=0)
    fighter.take_damage(3)
    assert fighter.heal(50) == 3
    assert fighter.hp == fighter.max_hp


def test_regeneration() -> None:
    fighter = Fighter(hp=10, attack=1, defense=0, regen_per_turn=1)
    fighter.take_damage(5)
    fighter.regenerate()
    assert fighter.hp == 6


# ---------------------------------------------------------------------------
# Бой в света
# ---------------------------------------------------------------------------
def arena() -> World:
    """Празна стая 10x7 с играч в (2, 3)."""
    return make_arena(10, 7, player_pos=(2, 3), seed=123)


def test_bump_into_enemy_attacks_instead_of_moving() -> None:
    world = arena()
    rat = create_enemy("rat", 3, 3)
    world.game_map.add_entity(rat)
    hp_before = rat.fighter.hp
    for _ in range(20):  # достатъчно опити, въпреки шанса за пропуск
        if not rat.is_alive:
            break
        assert BumpAction(world.player, 1, 0).perform(world)
    assert world.player.position == (2, 3)
    assert rat.fighter.hp < hp_before


def test_killing_enemy_makes_corpse_and_counts_kill() -> None:
    world = arena()
    rat = create_enemy("rat", 3, 3)
    world.game_map.add_entity(rat)
    rat.fighter.hp = 1
    while rat.is_alive:
        MeleeAction(world.player, 1, 0).perform(world)
    assert world.kills == 1
    assert not rat.blocks_movement and rat.ai is None
    assert rat.char == config.CORPSE_CHAR
    assert MoveAction(world.player, 1, 0).perform(world)  # трупът не блокира


def test_melee_into_empty_cell_is_invalid() -> None:
    world = arena()
    assert MeleeAction(world.player, 1, 0).perform(world) is False


def test_hostile_ai_attacks_adjacent_player() -> None:
    world = arena()
    goblin = create_enemy("goblin", 3, 3)
    world.game_map.add_entity(goblin)
    world.update_fov()
    assert isinstance(goblin.ai, HostileAI)
    assert isinstance(goblin.ai.decide(world), MeleeAction)


def test_hostile_ai_chases_visible_player() -> None:
    world = arena()
    goblin = create_enemy("goblin", 7, 3)
    world.game_map.add_entity(goblin)
    world.update_fov()
    goblin.ai.decide(world).perform(world)
    assert goblin.distance_to(2, 3) == 4  # приближил се е с 1 (прав или диагонален ход)


def test_hostile_ai_waits_if_player_never_seen() -> None:
    world = make_arena(20, 7, player_pos=(2, 3))
    world.game_map.set_tile(10, 1, tile.WALL)
    for y in range(1, 6):
        world.game_map.set_tile(10, y, tile.WALL)  # стена разделя стаята
    goblin = create_enemy("goblin", 15, 3)
    world.game_map.add_entity(goblin)
    world.update_fov()
    assert isinstance(goblin.ai.decide(world), WaitAction)


def test_turn_manager_enemies_act_after_player() -> None:
    world = arena()
    goblin = create_enemy("goblin", 7, 3)
    world.game_map.add_entity(goblin)
    world.update_fov()
    manager = TurnManager(world)
    assert manager.play_turn(WaitAction(world.player))
    assert world.turn == 1
    assert goblin.distance_to(*world.player.position) == 4


def test_invalid_player_action_does_not_advance_world() -> None:
    world = arena()
    goblin = create_enemy("goblin", 7, 3)
    world.game_map.add_entity(goblin)
    world.player.place(1, 1)
    world.update_fov()
    manager = TurnManager(world)
    assert not manager.play_turn(MoveAction(world.player, -1, 0))  # в стена
    assert world.turn == 0
    assert goblin.position == (7, 3)


def test_player_death_sets_game_over() -> None:
    world = arena()
    goblin = create_enemy("goblin", 3, 3)
    world.game_map.add_entity(goblin)
    world.update_fov()
    world.player.fighter.hp = 1
    manager = TurnManager(world)
    for _ in range(50):
        if world.game_over:
            break
        manager.play_turn(WaitAction(world.player))
    assert world.game_over
    assert "загина" in world.message_log.messages[-1].text


def test_new_game_spawns_enemies_outside_start_area() -> None:
    world = World.new_game(seed=77)
    enemies = [a for a in world.game_map.actors if a is not world.player]
    assert enemies
    for enemy in enemies:
        assert enemy.position not in world.game_map.start_area
        assert world.game_map.is_walkable(*enemy.position)

"""Тестове за прогресията, новите врагове, боса и цяла игра (Етап 7)."""

from __future__ import annotations

import pytest

import config
from components.ai import BossAI, RangedAI
from components.level import Level
from engine.actions import (
    Action,
    BumpAction,
    DescendAction,
    MeleeAction,
    MoveAction,
    RangedAttackAction,
    UseItemAction,
    WaitAction,
)
from engine.turn_manager import TurnManager
from engine.world import World, generate_floor
from entities.factories import create_enemy, create_player
from systems.pathfinding import find_path
from tests.helpers import make_arena
from world import connectivity, tile
from world.spawner import weights_for_floor


def arena(width: int = 16, height: int = 9) -> World:
    """Празна стая с играч в (2, 4)."""
    return make_arena(width, height, player_pos=(2, 4), seed=9)


def add_enemy(world: World, key: str, x: int, y: int):
    enemy = create_enemy(key, x, y)
    world.game_map.add_entity(enemy)
    world.update_fov()
    return enemy


# ---------------------------------------------------------------------------
# Опит и нива
# ---------------------------------------------------------------------------
def test_xp_formula() -> None:
    level = Level(level_up_base=50, level_up_factor=1.5)
    assert level.experience_to_next_level == 75
    level.current_level = 3
    assert level.experience_to_next_level == 225


def test_level_up_choices_change_stats() -> None:
    player = create_player()
    level, fighter = player.level, player.fighter
    assert level is not None
    level.add_xp(1000)
    level.increase_max_hp()
    assert fighter.max_hp == config.PLAYER_MAX_HP + config.LEVEL_UP_HP
    level.increase_attack()
    assert fighter.attack == config.PLAYER_ATTACK + config.LEVEL_UP_ATTACK
    level.increase_defense()
    assert fighter.defense == config.PLAYER_DEFENSE + config.LEVEL_UP_DEFENSE
    assert level.current_level == 4


def test_leftover_xp_carries_over() -> None:
    level = Level(level_up_base=50, level_up_factor=1.5)
    level.owner = create_player()
    assert level.add_xp(80)
    level.increase_attack()
    assert level.current_xp == 5 and level.current_level == 2
    assert not level.requires_level_up


def test_killing_enemy_gives_xp() -> None:
    world = arena()
    rat = add_enemy(world, "rat", 3, 4)
    rat.fighter.hp = 1
    while rat.is_alive:
        MeleeAction(world.player, 1, 0).perform(world)
    assert world.player.level.current_xp == config.ENEMIES["rat"].xp


# ---------------------------------------------------------------------------
# Нови врагове
# ---------------------------------------------------------------------------
def test_archer_shoots_from_distance_with_clear_line() -> None:
    world = arena()
    archer = add_enemy(world, "skeleton_archer", 6, 4)  # разстояние 4
    assert isinstance(archer.ai, RangedAI)
    assert isinstance(archer.ai.decide(world), RangedAttackAction)


def test_archer_retreats_when_too_close() -> None:
    world = arena()
    archer = add_enemy(world, "skeleton_archer", 4, 4)  # разстояние 2
    action = archer.ai.decide(world)
    assert isinstance(action, MoveAction)
    action.perform(world)
    assert archer.distance_to(*world.player.position) == 3


def test_archer_does_not_shoot_through_other_actors() -> None:
    world = arena()
    add_enemy(world, "rat", 4, 4)
    archer = add_enemy(world, "skeleton_archer", 6, 4)
    assert not world.clear_shot(archer.position, world.player.position)
    assert not isinstance(archer.ai.decide(world), RangedAttackAction)


def test_troll_regenerates_each_turn() -> None:
    world = arena(width=30)
    for y in range(1, 8):
        world.game_map.set_tile(15, y, tile.WALL)  # тролът не вижда играча
    troll = add_enemy(world, "troll", 25, 4)
    troll.fighter.take_damage(10)
    manager = TurnManager(world)
    for _ in range(3):
        manager.play_turn(WaitAction(world.player))
    assert troll.fighter.hp == troll.fighter.max_hp - 10 + 3


def test_boss_phase_two_summons_goblins_once() -> None:
    world = arena()
    boss = add_enemy(world, "boss", 8, 4)
    assert isinstance(boss.ai, BossAI)
    attack_before = boss.fighter.attack
    boss.fighter.hp = boss.fighter.max_hp // 2 - 1
    boss.ai.decide(world).perform(world)
    goblins = [a for a in world.game_map.actors if a.kind == "goblin"]
    assert len(goblins) == config.BOSS_SUMMON_COUNT
    assert boss.ai.phase == 2
    assert boss.fighter.attack == attack_before + config.BOSS_ENRAGE_ATTACK
    boss.ai.decide(world)  # втори път не призовава отново
    assert len([a for a in world.game_map.actors if a.kind == "goblin"]) == 2


def test_killing_boss_wins_the_game() -> None:
    world = arena()
    boss = add_enemy(world, "boss", 3, 4)
    boss.fighter.hp = 1
    while boss.is_alive:
        MeleeAction(world.player, 1, 0).perform(world)
    assert world.victory


# ---------------------------------------------------------------------------
# Етажи и спаунване
# ---------------------------------------------------------------------------
def test_spawn_tables_respect_floor() -> None:
    assert set(weights_for_floor(config.ENEMY_SPAWN_WEIGHTS, 1)) == {"rat", "goblin"}
    assert "troll" not in weights_for_floor(config.ENEMY_SPAWN_WEIGHTS, 6)
    assert "troll" in weights_for_floor(config.ENEMY_SPAWN_WEIGHTS, 7)
    assert "skeleton_archer" in weights_for_floor(config.ENEMY_SPAWN_WEIGHTS, 3)
    assert "orc" in weights_for_floor(config.ENEMY_SPAWN_WEIGHTS, 4)


@pytest.mark.parametrize("floor", range(1, config.BOSS_FLOOR + 1))
def test_every_floor_is_valid(floor: int) -> None:
    game_map = generate_floor(seed=2024, floor=floor)
    grid = game_map.walkable_grid()
    targets = [item.position for item in game_map.items]
    if game_map.stairs is not None:
        targets.append(game_map.stairs)
    assert connectivity.all_reachable(grid, game_map.player_start, targets)
    for actor in game_map.actors:
        assert game_map.is_walkable(*actor.position)


def test_boss_floor_has_boss_and_no_stairs() -> None:
    game_map = generate_floor(seed=5, floor=config.BOSS_FLOOR)
    assert game_map.stairs is None
    bosses = [a for a in game_map.actors if a.kind == config.BOSS_KEY]
    assert len(bosses) == 1
    assert game_map.rooms[-1].contains(*bosses[0].position)
    reachable = connectivity.flood_fill(game_map.walkable_grid(), game_map.player_start)
    assert bosses[0].position in reachable


# ---------------------------------------------------------------------------
# Цяла игра: прост бот минава от етаж 1 до победата
# ---------------------------------------------------------------------------
def bot_action(world: World) -> Action:
    """Проста стратегия: удряй съседни врагове, пий отвари, върви към целта."""
    player = world.player
    for enemy in world.visible_enemies():
        if player.distance_to(*enemy.position) == 1:
            return MeleeAction(player, enemy.x - player.x, enemy.y - player.y)
    if player.fighter.hp < player.fighter.max_hp // 3:
        for item in player.inventory.items:
            if item.consumable is not None and not item.consumable.needs_target:
                return UseItemAction(player, item)
    if world.player_on_stairs:
        return DescendAction(player)
    if world.game_map.stairs is not None:
        target = world.game_map.stairs
    else:
        target = next(a.position for a in world.game_map.actors if a.kind == config.BOSS_KEY)
    occupied = {a.position for a in world.game_map.actors if a is not player}
    path = find_path(world.game_map.walkable_grid(), player.position, target, occupied)
    if not path:
        return WaitAction(player)
    return BumpAction(player, path[0][0] - player.x, path[0][1] - player.y)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_full_game_can_be_played_from_floor_1_to_victory(seed: int) -> None:
    world = World.new_game(seed=seed)
    # Силен играч: тестваме, че механиките позволяват цяла игра, а не баланса.
    world.player.fighter.base_max_hp = 2000
    world.player.fighter.hp = 2000
    world.player.fighter.base_attack = 20
    manager = TurnManager(world)
    floors_seen = {world.floor}
    for _ in range(6000):
        if world.victory or world.game_over:
            break
        manager.play_turn(bot_action(world))
        floors_seen.add(world.floor)
        while world.player.level.requires_level_up:
            world.player.level.increase_defense()
    assert world.victory, f"Ботът спря на етаж {world.floor}"
    assert floors_seen == set(range(1, config.BOSS_FLOOR + 1))
    assert world.kills > 0

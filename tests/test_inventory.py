"""Тестове за предмети, инвентар и екипировка (Етап 6)."""

from __future__ import annotations

import config
from components.ai import ConfusedAI, HostileAI
from components.inventory import Inventory
from engine.actions import (
    DropItemAction,
    EquipAction,
    PickupAction,
    UseItemAction,
    WaitAction,
)
from engine.turn_manager import TurnManager
from engine.world import World
from entities.factories import create_enemy, create_item
from tests.helpers import make_arena


def arena() -> World:
    """Празна стая 12x9 с играч в (2, 4)."""
    return make_arena(12, 9, player_pos=(2, 4), seed=5)


def give(world: World, key: str):
    """Слага предмет директно в раницата на играча."""
    item = create_item(key)
    assert world.player.inventory is not None
    world.player.inventory.add(item)
    return item


# ---------------------------------------------------------------------------
# Раница
# ---------------------------------------------------------------------------
def test_inventory_capacity() -> None:
    inventory = Inventory(capacity=3)
    items = [create_item("small_potion") for _ in range(4)]
    assert all(inventory.add(item) for item in items[:3])
    assert inventory.is_full
    assert inventory.add(items[3]) is False
    assert len(inventory) == 3


def test_pickup_moves_item_from_map_to_inventory() -> None:
    world = arena()
    potion = create_item("small_potion", 2, 4)
    world.game_map.add_entity(potion)
    assert PickupAction(world.player).perform(world)
    assert potion in world.player.inventory
    assert potion not in world.game_map.entities


def test_pickup_with_nothing_on_floor_is_invalid() -> None:
    world = arena()
    assert PickupAction(world.player).perform(world) is False


def test_pickup_with_full_inventory_leaves_item() -> None:
    world = arena()
    world.player.inventory.capacity = 1
    give(world, "small_potion")
    potion = create_item("large_potion", 2, 4)
    world.game_map.add_entity(potion)
    assert PickupAction(world.player).perform(world) is False
    assert potion in world.game_map.entities


def test_drop_puts_item_under_player_and_unequips() -> None:
    world = arena()
    sword = give(world, "sword")
    EquipAction(world.player, sword).perform(world)
    assert DropItemAction(world.player, sword).perform(world)
    assert sword not in world.player.inventory
    assert sword.position == world.player.position
    assert not world.player.equipment.is_equipped(sword)
    assert world.player.fighter.attack == config.PLAYER_ATTACK


# ---------------------------------------------------------------------------
# Консумативи
# ---------------------------------------------------------------------------
def test_healing_does_not_exceed_max_hp() -> None:
    world = arena()
    fighter = world.player.fighter
    fighter.take_damage(5)
    potion = give(world, "large_potion")  # +25 HP, а липсват само 5
    assert UseItemAction(world.player, potion).perform(world)
    assert fighter.hp == fighter.max_hp
    assert potion not in world.player.inventory  # изразходвана


def test_healing_at_full_hp_is_refused_and_keeps_potion() -> None:
    world = arena()
    potion = give(world, "small_potion")
    assert UseItemAction(world.player, potion).perform(world) is False
    assert potion in world.player.inventory


def test_lightning_hits_nearest_visible_enemy() -> None:
    world = arena()
    near = create_enemy("goblin", 4, 4)
    far = create_enemy("goblin", 8, 4)
    world.game_map.add_entity(near)
    world.game_map.add_entity(far)
    world.update_fov()
    scroll = give(world, "lightning_scroll")
    assert UseItemAction(world.player, scroll).perform(world)
    assert not near.is_alive  # 20 щета > 10 HP
    assert far.fighter.hp == far.fighter.max_hp
    assert scroll not in world.player.inventory


def test_lightning_without_enemies_is_refused() -> None:
    world = arena()
    scroll = give(world, "lightning_scroll")
    assert UseItemAction(world.player, scroll).perform(world) is False
    assert scroll in world.player.inventory


def test_confusion_replaces_ai_and_restores_it() -> None:
    world = arena()
    goblin = create_enemy("goblin", 6, 4)
    world.game_map.add_entity(goblin)
    world.update_fov()
    original_ai = goblin.ai
    scroll = give(world, "confusion_scroll")
    assert UseItemAction(world.player, scroll, target=(6, 4)).perform(world)
    assert isinstance(goblin.ai, ConfusedAI)
    manager = TurnManager(world)
    for _ in range(config.CONFUSION_TURNS + 1):
        manager.play_turn(WaitAction(world.player))
    assert goblin.ai is original_ai
    assert isinstance(goblin.ai, HostileAI)


def test_confusion_on_empty_cell_is_refused() -> None:
    world = arena()
    scroll = give(world, "confusion_scroll")
    assert UseItemAction(world.player, scroll, target=(5, 5)).perform(world) is False
    assert scroll in world.player.inventory


# ---------------------------------------------------------------------------
# Екипировка
# ---------------------------------------------------------------------------
def test_equipment_changes_stats() -> None:
    world = arena()
    fighter = world.player.fighter
    sword = give(world, "sword")
    armor = give(world, "chain_mail")
    UseItemAction(world.player, sword).perform(world)
    UseItemAction(world.player, armor).perform(world)
    assert fighter.attack == config.PLAYER_ATTACK + 3
    assert fighter.defense == config.PLAYER_DEFENSE + 3
    # Повторно използване сваля предмета.
    UseItemAction(world.player, sword).perform(world)
    assert fighter.attack == config.PLAYER_ATTACK


def test_new_weapon_replaces_old_in_same_slot() -> None:
    world = arena()
    dagger = give(world, "dagger")
    axe = give(world, "axe")
    EquipAction(world.player, dagger).perform(world)
    EquipAction(world.player, axe).perform(world)
    equipment = world.player.equipment
    assert equipment.is_equipped(axe) and not equipment.is_equipped(dagger)
    assert world.player.fighter.attack == config.PLAYER_ATTACK + 5


def test_all_config_items_can_be_created() -> None:
    for key, data in config.ITEMS.items():
        item = create_item(key)
        assert item.name == data.name
        assert (item.consumable is None) != (item.equippable is None)


def test_new_game_spawns_items_on_floor() -> None:
    world = World.new_game(seed=21)
    items = world.game_map.items
    assert items
    for item in items:
        assert world.game_map.is_walkable(*item.position)
        assert item.position != world.game_map.stairs

"""Тестове за Entity/Actor, екипировката, ConfusedAI и TurnManager."""

from __future__ import annotations

import config
from components.ai import ConfusedAI, HostileAI
from components.equipment import Equipment
from components.equippable import EquipmentSlot
from engine.actions import BumpAction, DescendAction, WaitAction
from engine.turn_manager import TurnManager
from engine.world import World
from entities.entity import Entity, RenderOrder
from entities.factories import create_enemy, create_item, create_player
from tests.helpers import make_arena


def test_entity_move_place_distance() -> None:
    entity = Entity(1, 1, "x", config.COLOR_WHITE, "тест")
    entity.move(2, -1)
    assert entity.position == (3, 0)
    entity.place(10, 10)
    assert entity.distance_to(13, 7) == 3  # Chebyshev


def test_actor_components_know_their_owner() -> None:
    player = create_player()
    for component in (player.fighter, player.inventory, player.equipment, player.level):
        assert component.owner is player
    goblin = create_enemy("goblin", 0, 0)
    assert goblin.ai.owner is goblin and goblin.kind == "goblin"


def test_corpse_properties() -> None:
    rat = create_enemy("rat", 0, 0)
    rat.fighter.take_damage(100)
    rat.become_corpse()
    assert rat.render_order == RenderOrder.CORPSE
    assert not rat.blocks_movement and rat.ai is None
    assert "Плъх" in rat.name


def test_equipment_slots_and_bonus() -> None:
    equipment = Equipment()
    sword, plate = create_item("sword"), create_item("plate_armor")
    assert equipment.equip(sword) is None
    assert equipment.equip(plate) is None
    assert equipment.slots[EquipmentSlot.WEAPON] is sword
    assert equipment.bonus("attack") == 3 and equipment.bonus("defense") == 5
    assert equipment.bonus("max_hp") == 0
    equipment.unequip(sword)
    assert equipment.bonus("attack") == 0
    assert equipment.equip(plate) is None  # повторно екипиране на същия предмет


def test_confused_enemy_moves_randomly_and_can_hit_others() -> None:
    world = make_arena(8, 8, player_pos=(1, 1))
    goblin = create_enemy("goblin", 4, 4)
    world.game_map.add_entity(goblin)
    goblin.replace_ai(ConfusedAI(goblin.ai, turns=3))
    for _ in range(3):
        action = goblin.ai.decide(world)
        assert isinstance(action, BumpAction)
        action.perform(world)
    assert isinstance(goblin.ai.decide(world), WaitAction)  # времето изтече
    assert isinstance(goblin.ai, HostileAI)


def test_descending_skips_enemy_turns() -> None:
    world = World.new_game(seed=12)
    world.player.place(*world.game_map.stairs)
    manager = TurnManager(world)
    assert manager.play_turn(DescendAction(world.player))
    assert world.floor == 2 and world.max_floor == 2
    # Новите врагове не са се помръднали: всички са извън стартовата зона.
    for enemy in world.game_map.actors:
        if enemy is not world.player:
            assert enemy.position not in world.game_map.start_area


def test_player_tile_messages() -> None:
    world = make_arena()
    world.game_map.add_entity(create_item("sword", 3, 4))
    BumpAction(world.player, 1, 0).perform(world)
    assert "Меч" in world.message_log.messages[-1].text

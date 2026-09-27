"""Действия (Command pattern).

Всяко действие е обект с метод `perform(world)`. И играчът (чрез InputHandler), и
изкуственият интелект на враговете създават такива обекти. Така логиката за "какво се
случва" е на едно място, независимо кой е поискал действието.

`perform` връща True, ако действието е изразходвало ход, и False, ако е невалидно
(например ход в стена) – тогава светът не се движи.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import config
from systems import combat

if TYPE_CHECKING:
    from engine.world import World
    from entities.actor import Actor
    from entities.entity import Entity
    from entities.item import Item

Point = tuple[int, int]


class Action:
    """Базов клас за всички действия.

    Attributes:
        entity: Обектът, който извършва действието.
    """

    def __init__(self, entity: Entity) -> None:
        self.entity = entity

    def perform(self, world: World) -> bool:
        """Изпълнява действието.

        Args:
            world: Текущото състояние на играта.

        Returns:
            True, ако е изразходван ход.
        """
        raise NotImplementedError


class WaitAction(Action):
    """Пропускане на ход."""

    def perform(self, world: World) -> bool:
        """Не прави нищо, но изразходва ход."""
        return True


class DescendAction(Action):
    """Слизане по стълбите надолу."""

    def perform(self, world: World) -> bool:
        """Слиза, ако играчът е на стълбите; иначе действието е невалидно."""
        if not world.player_on_stairs:
            world.message_log.add("Тук няма стълби надолу.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        world.descend()
        return True


class ActionWithDirection(Action):
    """Действие с посока (dx, dy)."""

    def __init__(self, entity: Entity, dx: int, dy: int) -> None:
        super().__init__(entity)
        self.dx = dx
        self.dy = dy

    @property
    def destination(self) -> tuple[int, int]:
        """Целевата клетка."""
        return self.entity.x + self.dx, self.entity.y + self.dy


class MoveAction(ActionWithDirection):
    """Преместване с една клетка."""

    def perform(self, world: World) -> bool:
        """Мести обекта, ако целта е проходима и свободна."""
        dest_x, dest_y = self.destination
        if not world.game_map.is_walkable(dest_x, dest_y):
            return False
        if world.game_map.get_blocking_entity_at(dest_x, dest_y) is not None:
            return False
        self.entity.move(self.dx, self.dy)
        if self.entity is world.player:
            world.describe_player_tile()
        return True


class MeleeAction(ActionWithDirection):
    """Атака в съседна клетка."""

    def perform(self, world: World) -> bool:
        """Атакува съществото в целевата клетка (ако има такова)."""
        target = world.game_map.get_actor_at(*self.destination)
        attacker: Actor = self.entity  # type: ignore[assignment]
        if target is None or target is attacker:
            return False
        attack_with_message(world, attacker, target)
        return True


class BumpAction(ActionWithDirection):
    """"Блъскане" в посока: атака, ако там има същество, иначе движение.

    Така играчът атакува просто като се опита да влезе в клетката на врага.
    """

    def perform(self, world: World) -> bool:
        """Избира и изпълнява MeleeAction или MoveAction."""
        if world.game_map.get_actor_at(*self.destination) is not None:
            return MeleeAction(self.entity, self.dx, self.dy).perform(world)
        return MoveAction(self.entity, self.dx, self.dy).perform(world)


class RangedAttackAction(Action):
    """Изстрел по цел на разстояние (скелет стрелец)."""

    def __init__(self, entity: Entity, target: Actor) -> None:
        super().__init__(entity)
        self.target = target

    def perform(self, world: World) -> bool:
        """Стреля, ако целта е жива и има чиста линия."""
        attacker: Actor = self.entity  # type: ignore[assignment]
        if not self.target.is_alive or not world.clear_shot(attacker.position,
                                                             self.target.position):
            return False
        attack_with_message(world, attacker, self.target, ranged=True)
        return True


# ---------------------------------------------------------------------------
# Предмети
# ---------------------------------------------------------------------------
class PickupAction(Action):
    """Вдигане на предмет от земята."""

    def perform(self, world: World) -> bool:
        """Слага първия предмет под играча в раницата."""
        actor: Actor = self.entity  # type: ignore[assignment]
        item = world.game_map.item_at(actor.x, actor.y)
        if item is None:
            world.message_log.add("Тук няма нищо за вдигане.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        if actor.inventory is None or not actor.inventory.add(item):
            world.message_log.add("Раницата ти е пълна.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        world.game_map.remove_entity(item)
        world.message_log.add(f"Вдигаш: {item.name}.", config.COLOR_MSG_ITEM)
        return True


class ItemAction(Action):
    """Действие с конкретен предмет от раницата (и евентуално целева клетка)."""

    def __init__(self, entity: Entity, item: Item, target: Point | None = None) -> None:
        super().__init__(entity)
        self.item = item
        self.target = target


class UseItemAction(ItemAction):
    """Използване: консумативите се изразходват, екипировката се слага/сваля."""

    def perform(self, world: World) -> bool:
        """Прилага ефекта на предмета."""
        actor: Actor = self.entity  # type: ignore[assignment]
        if self.item.equippable is not None:
            return EquipAction(actor, self.item).perform(world)
        consumable = self.item.consumable
        if consumable is None:
            world.message_log.add("Това не може да се използва.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        if not consumable.activate(actor, world, self.target):
            return False
        consumable.consume(actor)
        return True


class EquipAction(ItemAction):
    """Екипиране или сваляне на предмет (превключване)."""

    def perform(self, world: World) -> bool:
        """Ако е екипиран – сваля го; иначе го слага (и сваля стария в слота)."""
        actor: Actor = self.entity  # type: ignore[assignment]
        if actor.equipment is None or self.item.equippable is None:
            return False
        if actor.equipment.is_equipped(self.item):
            actor.equipment.unequip(self.item)
            world.message_log.add(f"Сваляш: {self.item.name}.", config.COLOR_MSG_ITEM)
            return True
        previous = actor.equipment.equip(self.item)
        if previous is not None:
            world.message_log.add(f"Сваляш: {previous.name}.", config.COLOR_MSG_ITEM)
        world.message_log.add(f"Екипираш: {self.item.name}.", config.COLOR_MSG_ITEM)
        return True


class DropItemAction(ItemAction):
    """Изхвърляне на предмет на земята."""

    def perform(self, world: World) -> bool:
        """Маха предмета от раницата (и екипировката) и го слага под играча."""
        actor: Actor = self.entity  # type: ignore[assignment]
        if actor.inventory is None or self.item not in actor.inventory:
            return False
        if actor.equipment is not None:
            actor.equipment.unequip(self.item)
        actor.inventory.remove(self.item)
        self.item.place(actor.x, actor.y)
        world.game_map.add_entity(self.item)
        world.message_log.add(f"Изхвърляш: {self.item.name}.", config.COLOR_MSG_ITEM)
        return True


# ---------------------------------------------------------------------------
# Помощни функции за бой (ползват се и от свитъците, и от стрелците)
# ---------------------------------------------------------------------------
def attack_with_message(world: World, attacker: Actor, target: Actor,
                        ranged: bool = False) -> combat.AttackResult:
    """Изпълнява атака, записва съобщение и обработва смъртта на целта."""
    result = combat.resolve_attack(attacker.fighter.attack, target.fighter.defense, world.rng)
    text, color = describe_attack(world, attacker, target, result)
    if ranged:
        text = f"Стрела! {text}"

    world.message_log.add(text, color)
    if not result.missed:
        target.fighter.take_damage(result.damage)
        if target.fighter.is_dead:
            world.handle_death(target)
    return result


def describe_attack(world: World, attacker: Actor, target: Actor,
                    result: combat.AttackResult) -> tuple[str, config.Color]:
    """Текст и цвят на съобщението за атака (от гледна точка на играча)."""
    player = world.player
    if result.missed:
        if attacker is player:
            return f"Пропускаш {target.name}.", config.COLOR_MSG_MISS
        return f"{attacker.name} пропуска.", config.COLOR_MSG_MISS
    if attacker is player:
        text = f"Удряш {target.name} за {result.damage} щета."
        color = config.COLOR_MSG_PLAYER_ATTACK
    elif target is player:
        text = f"{attacker.name} те удря за {result.damage} щета."
        color = config.COLOR_MSG_ENEMY_ATTACK
    else:
        text = f"{attacker.name} удря {target.name} за {result.damage} щета."
        color = config.COLOR_MSG_PLAYER_ATTACK
    if result.critical:
        return f"Критичен удар! {text}", config.COLOR_MSG_CRIT
    return text, color

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


# ---------------------------------------------------------------------------
# Помощни функции за бой (ползват се и от свитъците, и от стрелците)
# ---------------------------------------------------------------------------
def attack_with_message(world: World, attacker: Actor, target: Actor) -> combat.AttackResult:
    """Изпълнява атака, записва съобщение и обработва смъртта на целта."""
    result = combat.resolve_attack(attacker.fighter.attack, target.fighter.defense, world.rng)
    text, color = describe_attack(world, attacker, target, result)
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

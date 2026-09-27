"""Компоненти Consumable: ефекти на предмети за еднократна употреба.

Всеки клас имплементира `activate(...)`. Ако ефектът е успешен, предметът се изразходва
(маха се от раницата) и ходът се брои. При неуспех (напр. няма враг наблизо) предметът
остава и ходът НЕ се губи.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import config
from components.ai import ConfusedAI

if TYPE_CHECKING:
    from engine.world import World
    from entities.actor import Actor
    from entities.item import Item

Point = tuple[int, int]


class Consumable:
    """Базов клас.

    Attributes:
        owner: Предметът.
        needs_target: Дали играчът трябва да избере клетка (свитък на объркването).
    """

    needs_target = False

    def __init__(self) -> None:
        self.owner: Item | None = None

    def activate(self, consumer: Actor, world: World, target: Point | None = None) -> bool:
        """Прилага ефекта. Връща True при успех."""
        raise NotImplementedError

    def consume(self, consumer: Actor) -> None:
        """Маха предмета от раницата след успешна употреба."""
        if consumer.inventory is not None and self.owner is not None:
            consumer.inventory.remove(self.owner)


class HealingConsumable(Consumable):
    """Лечебна отвара."""

    def __init__(self, amount: int) -> None:
        super().__init__()
        self.amount = amount

    def activate(self, consumer: Actor, world: World, target: Point | None = None) -> bool:
        """Лекува с `amount`, но не над максимума."""
        healed = consumer.fighter.heal(self.amount)
        if healed <= 0:
            world.message_log.add("Вече си напълно здрав.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        world.message_log.add(f"Изпиваш отварата и възстановяваш {healed} HP.",
                              config.COLOR_MSG_HEAL)
        return True


class LightningConsumable(Consumable):
    """Свитък на мълнията: удря най-близкия видим враг."""

    def __init__(self, damage: int, max_range: int) -> None:
        super().__init__()
        self.damage = damage
        self.max_range = max_range

    def activate(self, consumer: Actor, world: World, target: Point | None = None) -> bool:
        """Намира най-близкия видим враг в обхват и му нанася `damage`."""
        candidates = [e for e in world.visible_enemies()
                      if consumer.distance_to(*e.position) <= self.max_range]
        if not candidates:
            world.message_log.add("Няма враг наблизо.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        enemy = min(candidates, key=lambda e: (consumer.distance_to(*e.position), e.position))
        world.message_log.add(
            f"Мълния поразява {enemy.name} за {self.damage} щета!", config.COLOR_MSG_MAGIC)
        enemy.fighter.take_damage(self.damage)
        if enemy.fighter.is_dead:
            world.handle_death(enemy)
        return True


class ConfusionConsumable(Consumable):
    """Свитък на объркването: избраният враг се движи случайно N хода."""

    needs_target = True

    def __init__(self, turns: int) -> None:
        super().__init__()
        self.turns = turns

    def activate(self, consumer: Actor, world: World, target: Point | None = None) -> bool:
        """Обърква съществото в `target` (трябва да е видимо и да не е играчът)."""
        if target is None or not world.game_map.is_visible(*target):
            world.message_log.add("Не виждаш тази клетка.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        enemy = world.game_map.get_actor_at(*target)
        if enemy is None or enemy is consumer:
            world.message_log.add("Там няма враг.", config.COLOR_MSG_IMPOSSIBLE)
            return False
        enemy.replace_ai(ConfusedAI(enemy.ai, self.turns))
        world.message_log.add(f"{enemy.name} изглежда объркан!", config.COLOR_MSG_MAGIC)
        return True

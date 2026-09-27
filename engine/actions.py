"""Действия (Command pattern).

Всяко действие е обект с метод `perform(world)`. И играчът (чрез InputHandler), и
изкуственият интелект на враговете създават такива обекти. Така логиката за "какво се
случва" е на едно място, независимо кой е поискал действието.

`perform` връща True, ако действието е изразходвало ход, и False, ако е невалидно
(например ход в стена) – тогава светът не се движи.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.world import World
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

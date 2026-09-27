"""Компонент Inventory: раницата на играча."""

from __future__ import annotations

from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from entities.actor import Actor
    from entities.item import Item


class Inventory:
    """Списък от предмети с ограничен капацитет.

    Attributes:
        owner: Собственикът.
        capacity: Максимален брой предмети.
        items: Предметите (редът е важен – буквите a, b, c... в менюто).
    """

    def __init__(self, capacity: int = config.INVENTORY_CAPACITY) -> None:
        self.owner: Actor | None = None
        self.capacity = capacity
        self.items: list[Item] = []

    @property
    def is_full(self) -> bool:
        """Дали раницата е пълна."""
        return len(self.items) >= self.capacity

    def add(self, item: Item) -> bool:
        """Добавя предмет. Връща False, ако няма място."""
        if self.is_full:
            return False
        self.items.append(item)
        return True

    def remove(self, item: Item) -> None:
        """Премахва предмет (ако го има)."""
        if item in self.items:
            self.items.remove(item)

    def __contains__(self, item: object) -> bool:
        return item in self.items

    def __len__(self) -> int:
        return len(self.items)

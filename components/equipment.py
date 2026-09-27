"""Компонент Equipment: какво е екипирал играчът."""

from __future__ import annotations

from typing import TYPE_CHECKING

from components.equippable import EquipmentSlot

if TYPE_CHECKING:
    from entities.actor import Actor
    from entities.item import Item


class Equipment:
    """По един предмет на слот (оръжие, броня).

    Fighter пита `bonus(stat)` всеки път, когато му трябва атака/защита – така
    характеристиките винаги отразяват текущата екипировка.

    Attributes:
        owner: Собственикът.
        slots: Слот → екипиран предмет (или None).
    """

    def __init__(self) -> None:
        self.owner: Actor | None = None
        self.slots: dict[EquipmentSlot, Item | None] = {slot: None for slot in EquipmentSlot}

    def bonus(self, stat: str) -> int:
        """Сумата от бонусите на всички екипирани предмети за `stat`."""
        return sum(
            item.equippable.bonus(stat)
            for item in self.slots.values()
            if item is not None and item.equippable is not None
        )

    def is_equipped(self, item: Item) -> bool:
        """Дали предметът е екипиран."""
        return item in self.slots.values()

    def equip(self, item: Item) -> Item | None:
        """Екипира предмета. Връща предмета, който е бил в слота преди това (или None)."""
        assert item.equippable is not None, "Предметът не може да се екипира"
        slot = item.equippable.slot
        previous = self.slots[slot]
        self.slots[slot] = item
        return previous if previous is not item else None

    def unequip(self, item: Item) -> None:
        """Сваля предмета (ако е екипиран)."""
        for slot, equipped in self.slots.items():
            if equipped is item:
                self.slots[slot] = None

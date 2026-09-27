"""Компонент Equippable: предмет, който може да се облече/хване."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.item import Item


class EquipmentSlot(Enum):
    """Слотове за екипировка."""

    WEAPON = "оръжие"
    ARMOR = "броня"


class Equippable:
    """Бонуси, които предметът дава, докато е екипиран.

    Attributes:
        owner: Предметът.
        slot: В кой слот се слага.
        attack_bonus: Добавка към атаката.
        defense_bonus: Добавка към защитата.
    """

    def __init__(self, slot: EquipmentSlot, attack_bonus: int = 0, defense_bonus: int = 0) -> None:
        self.owner: Item | None = None
        self.slot = slot
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus

    def bonus(self, stat: str) -> int:
        """Бонус за характеристика ("attack", "defense", "max_hp")."""
        return {"attack": self.attack_bonus, "defense": self.defense_bonus}.get(stat, 0)

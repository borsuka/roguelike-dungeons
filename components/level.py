"""Компонент Level: опит и нива на играча."""

from __future__ import annotations

from typing import TYPE_CHECKING

import config

if TYPE_CHECKING:
    from components.fighter import Fighter
    from entities.actor import Actor


class Level:
    """Натрупва опит; при достатъчно опит играчът избира подобрение.

    Нужният опит за следващо ниво е `base * ниво * factor` – всяко ниво иска повече.

    Attributes:
        owner: Собственикът.
        current_level: Текущото ниво (от 1).
        current_xp: Опитът, натрупан към следващото ниво.
        level_up_base: Базата във формулата.
        level_up_factor: Множителят във формулата.
    """

    def __init__(self, level_up_base: int = config.LEVEL_UP_BASE,
                 level_up_factor: float = config.LEVEL_UP_FACTOR) -> None:
        self.owner: Actor | None = None
        self.current_level = 1
        self.current_xp = 0
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor

    @property
    def experience_to_next_level(self) -> int:
        """Колко опит е нужен за следващото ниво."""
        return int(self.level_up_base * self.current_level * self.level_up_factor)

    @property
    def requires_level_up(self) -> bool:
        """Дали е натрупан достатъчно опит за ново ниво."""
        return self.current_xp >= self.experience_to_next_level

    def add_xp(self, xp: int) -> bool:
        """Добавя опит. Връща True, ако вече може да се качи ниво."""
        self.current_xp += max(0, xp)
        return self.requires_level_up

    def _increase_level(self) -> None:
        """Изразходва опита за едно ниво и увеличава нивото."""
        self.current_xp -= self.experience_to_next_level
        self.current_level += 1

    def _fighter(self) -> Fighter:
        """Fighter компонентът на собственика."""
        assert self.owner is not None, "Level не е закачен към Actor"
        return self.owner.fighter

    def increase_max_hp(self, amount: int = config.LEVEL_UP_HP) -> None:
        """Избор при ново ниво: +max HP (и лекува със същото количество)."""
        fighter = self._fighter()
        fighter.base_max_hp += amount
        fighter.heal(amount)
        self._increase_level()

    def increase_attack(self, amount: int = config.LEVEL_UP_ATTACK) -> None:
        """Избор при ново ниво: +атака."""
        self._fighter().base_attack += amount
        self._increase_level()

    def increase_defense(self, amount: int = config.LEVEL_UP_DEFENSE) -> None:
        """Избор при ново ниво: +защита."""
        self._fighter().base_defense += amount
        self._increase_level()

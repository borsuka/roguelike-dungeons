"""Компонент Fighter: всичко, свързано с живот и бой."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.actor import Actor


class Fighter:
    """Бойни характеристики на Actor.

    Базовите стойности се пазят отделно, а `attack`/`defense`/`max_hp` са свойства –
    така екипировката и нивата могат да ги променят, без да презаписват основата.

    Attributes:
        owner: Actor, към когото е закачен компонентът.
        base_max_hp: Максимален живот без бонуси.
        base_attack: Атака без бонуси.
        base_defense: Защита без бонуси.
        xp_reward: Опит, който дава при смърт.
        regen_per_turn: Колко HP възстановява всеки ход (напр. трол).
    """

    def __init__(self, hp: int, attack: int, defense: int, xp_reward: int = 0,
                 regen_per_turn: int = 0) -> None:
        self.owner: Actor | None = None
        self.base_max_hp = hp
        self.base_attack = attack
        self.base_defense = defense
        self.xp_reward = xp_reward
        self.regen_per_turn = regen_per_turn
        self._hp = hp

    # ------------------------------------------------------------------ бонуси
    def _bonus(self, stat: str) -> int:
        """Бонус от екипировката на собственика (0, ако няма екипировка)."""
        equipment = getattr(self.owner, "equipment", None)
        return equipment.bonus(stat) if equipment is not None else 0

    @property
    def max_hp(self) -> int:
        """Максимален живот (базов + бонуси)."""
        return self.base_max_hp + self._bonus("max_hp")

    @property
    def attack(self) -> int:
        """Атака (базова + бонуси)."""
        return self.base_attack + self._bonus("attack")

    @property
    def defense(self) -> int:
        """Защита (базова + бонуси)."""
        return self.base_defense + self._bonus("defense")

    # ------------------------------------------------------------------ живот
    @property
    def hp(self) -> int:
        """Текущ живот, винаги в [0, max_hp]."""
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))

    @property
    def is_dead(self) -> bool:
        """True, ако животът е 0."""
        return self._hp <= 0

    def take_damage(self, amount: int) -> int:
        """Намалява живота. Връща реално нанесената щета."""
        before = self._hp
        self.hp = self._hp - max(0, amount)
        return before - self._hp

    def heal(self, amount: int) -> int:
        """Лекува, без да надвишава max_hp. Връща реално възстановените HP."""
        before = self._hp
        self.hp = self._hp + max(0, amount)
        return self._hp - before

    def regenerate(self) -> int:
        """Регенерация в началото на хода (0 за повечето врагове)."""
        if self.is_dead or self.regen_per_turn <= 0:
            return 0
        return self.heal(self.regen_per_turn)

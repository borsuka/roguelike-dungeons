"""Формула за щета при атака.

Щета = max(1, атака − защита) ± DAMAGE_VARIANCE, но никога под 1.
С шанс CRIT_CHANCE щетата се умножава по CRIT_MULTIPLIER (критичен удар).
С шанс MISS_CHANCE атаката пропуска изцяло.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import config


@dataclass(frozen=True)
class AttackResult:
    """Резултат от една атака.

    Attributes:
        damage: Нанесена щета (0 при пропуск).
        critical: Дали е критичен удар.
        missed: Дали атаката е пропуснала.
    """

    damage: int
    critical: bool
    missed: bool


def roll_damage(attack: int, defense: int, rng: random.Random) -> tuple[int, bool]:
    """Изчислява щетата при попадение.

    Args:
        attack: Атака на нападателя.
        defense: Защита на защитника.
        rng: Генератор на случайни числа.

    Returns:
        (щета, критичен ли е ударът). Щетата е винаги ≥ 1.
    """
    base = max(1, attack - defense)
    variance = rng.randint(-config.DAMAGE_VARIANCE, config.DAMAGE_VARIANCE)
    damage = max(1, base + variance)
    critical = rng.random() < config.CRIT_CHANCE
    if critical:
        damage *= config.CRIT_MULTIPLIER
    return damage, critical


def resolve_attack(attack: int, defense: int, rng: random.Random) -> AttackResult:
    """Цяла атака: първо проверка за пропуск, после щета."""
    if rng.random() < config.MISS_CHANCE:
        return AttackResult(damage=0, critical=False, missed=True)
    damage, critical = roll_damage(attack, defense, rng)
    return AttackResult(damage=damage, critical=critical, missed=False)

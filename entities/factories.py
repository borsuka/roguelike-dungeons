"""Фабрики: създаване на играча и враговете по таблиците в config.py.

Данните (HP, атака, символ...) са в config; тук е само "сглобяването" на компонентите.
Така нов враг се добавя с един ред в config, без нов клас.
"""

from __future__ import annotations

import config
from components.ai import BaseAI, HostileAI
from components.fighter import Fighter
from entities.actor import Actor


def create_player(x: int = 0, y: int = 0) -> Actor:
    """Създава играча."""
    fighter = Fighter(config.PLAYER_MAX_HP, config.PLAYER_ATTACK, config.PLAYER_DEFENSE)
    return Actor(x, y, config.PLAYER_CHAR, config.COLOR_PLAYER, config.PLAYER_NAME, fighter)


def make_ai(kind: str) -> BaseAI:
    """AI по име от таблицата с врагове."""
    if kind == "hostile":
        return HostileAI()
    raise ValueError(f"Непознат тип AI: {kind}")


def create_enemy(key: str, x: int, y: int) -> Actor:
    """Създава враг по ключ от `config.ENEMIES` (напр. "goblin")."""
    data = config.ENEMIES[key]
    fighter = Fighter(data.hp, data.attack, data.defense, xp_reward=data.xp,
                      regen_per_turn=data.regen)
    return Actor(x, y, data.char, data.color, data.name, fighter, ai=make_ai(data.ai))

"""Фабрики: създаване на играча и враговете по таблиците в config.py.

Данните (HP, атака, символ...) са в config; тук е само "сглобяването" на компонентите.
Така нов враг се добавя с един ред в config, без нов клас.
"""

from __future__ import annotations

import config
from components.ai import BaseAI, HostileAI
from components.consumable import (
    ConfusionConsumable,
    Consumable,
    HealingConsumable,
    LightningConsumable,
)
from components.equipment import Equipment
from components.equippable import EquipmentSlot, Equippable
from components.fighter import Fighter
from components.inventory import Inventory
from entities.actor import Actor
from entities.item import Item


def create_player(x: int = 0, y: int = 0) -> Actor:
    """Създава играча."""
    fighter = Fighter(config.PLAYER_MAX_HP, config.PLAYER_ATTACK, config.PLAYER_DEFENSE)
    return Actor(x, y, config.PLAYER_CHAR, config.COLOR_PLAYER, config.PLAYER_NAME, fighter,
                 inventory=Inventory(), equipment=Equipment())


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


def make_consumable(data: config.ItemDef) -> Consumable:
    """Consumable компонент според вида предмет."""
    if data.kind == "heal":
        return HealingConsumable(data.power)
    if data.kind == "lightning":
        return LightningConsumable(data.power, config.LIGHTNING_RANGE)
    if data.kind == "confusion":
        return ConfusionConsumable(data.power)
    raise ValueError(f"Непознат вид консуматив: {data.kind}")


def create_item(key: str, x: int = 0, y: int = 0) -> Item:
    """Създава предмет по ключ от `config.ITEMS` (напр. "sword")."""
    data = config.ITEMS[key]
    if data.kind == "weapon":
        equippable = Equippable(EquipmentSlot.WEAPON, attack_bonus=data.power)
        return Item(x, y, data.char, data.color, data.name, equippable=equippable)
    if data.kind == "armor":
        equippable = Equippable(EquipmentSlot.ARMOR, defense_bonus=data.power)
        return Item(x, y, data.char, data.color, data.name, equippable=equippable)
    return Item(x, y, data.char, data.color, data.name, consumable=make_consumable(data))

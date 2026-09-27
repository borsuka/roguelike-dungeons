"""Превръщане на натиснат клавиш в действие (Action) или команда за интерфейса."""

from __future__ import annotations

from enum import Enum, auto

import pygame

import config
from engine.actions import Action, BumpAction, DescendAction, PickupAction, WaitAction
from entities.entity import Entity


class Command(Enum):
    """Команди, които не са ход в играта, а смяна на екран."""

    PAUSE = auto()
    INVENTORY = auto()
    DROP = auto()
    SHOW_LOG = auto()


def key_name(event: pygame.event.Event) -> str:
    """Името на клавиша (напр. "up", "w", "[8]")."""
    return pygame.key.name(event.key)


def translate_key(event: pygame.event.Event, player: Entity) -> Action | Command | None:
    """Връща действието/командата за натиснатия клавиш или None.

    Args:
        event: pygame KEYDOWN събитие.
        player: Играчът, който ще извърши действието.
    """
    name = key_name(event)
    # ">" е Shift + "." – проверяваме символа преди името на клавиша.
    if event.unicode == config.DESCEND_CHAR or name in config.CONFIRM_KEYS:
        return DescendAction(player)
    # Главно "D" (Shift+d) е изхвърляне; малко "d" остава движение надясно (WASD).
    if event.unicode == config.DROP_CHAR:
        return Command.DROP
    if name == config.INVENTORY_KEY:
        return Command.INVENTORY
    if name == config.LOG_KEY:
        return Command.SHOW_LOG
    if name == config.PICKUP_KEY:
        return PickupAction(player)
    if name == config.ESCAPE_KEY:
        return Command.PAUSE
    if name in config.MOVE_KEYS:
        dx, dy = config.MOVE_KEYS[name]
        return BumpAction(player, dx, dy)
    if name in config.WAIT_KEYS:
        return WaitAction(player)
    return None

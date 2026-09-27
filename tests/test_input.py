"""Тестове за превода клавиш → действие (изисква pygame, но без прозорец)."""

from __future__ import annotations

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402
import pytest  # noqa: E402

from engine.actions import (  # noqa: E402
    BumpAction,
    DescendAction,
    PickupAction,
    WaitAction,
)
from engine.input_handler import Command, translate_key  # noqa: E402
from engine.smoke import key_event  # noqa: E402
from entities.factories import create_player  # noqa: E402

pygame.init()
PLAYER = create_player()


@pytest.mark.parametrize("key, char, delta", [
    (pygame.K_UP, "", (0, -1)), (pygame.K_w, "w", (0, -1)), (pygame.K_KP8, "8", (0, -1)),
    (pygame.K_d, "d", (1, 0)), (pygame.K_c, "c", (1, 1)), (pygame.K_KP7, "7", (-1, -1)),
    (pygame.K_HOME, "", (-1, -1)), (pygame.K_PAGEDOWN, "", (1, 1)),
])
def test_movement_keys(key: int, char: str, delta: tuple[int, int]) -> None:
    action = translate_key(key_event(key, char), PLAYER)
    assert isinstance(action, BumpAction)
    assert (action.dx, action.dy) == delta


@pytest.mark.parametrize("key, char", [
    (pygame.K_PERIOD, "."), (pygame.K_SPACE, " "), (pygame.K_KP5, "5"),
])
def test_wait_keys(key: int, char: str) -> None:
    assert isinstance(translate_key(key_event(key, char), PLAYER), WaitAction)


def test_shift_period_descends_but_period_waits() -> None:
    assert isinstance(translate_key(key_event(pygame.K_PERIOD, ">"), PLAYER), DescendAction)
    assert isinstance(translate_key(key_event(pygame.K_RETURN, "\r"), PLAYER), DescendAction)


def test_lowercase_d_moves_uppercase_d_drops() -> None:
    assert isinstance(translate_key(key_event(pygame.K_d, "d"), PLAYER), BumpAction)
    assert translate_key(key_event(pygame.K_d, "D"), PLAYER) is Command.DROP


def test_commands() -> None:
    assert translate_key(key_event(pygame.K_i, "i"), PLAYER) is Command.INVENTORY
    assert translate_key(key_event(pygame.K_v, "v"), PLAYER) is Command.SHOW_LOG
    assert translate_key(key_event(pygame.K_ESCAPE), PLAYER) is Command.PAUSE
    assert isinstance(translate_key(key_event(pygame.K_g, "g"), PLAYER), PickupAction)


def test_unknown_key_returns_none() -> None:
    assert translate_key(key_event(pygame.K_F5), PLAYER) is None

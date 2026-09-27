"""Headless smoke test: пуска истинската игра без прозорец и натиска случайни клавиши.

Целта е да се хване всяка грешка (exception) при реална комбинация от екрани и действия.
Трябва да се извиква със `SDL_VIDEODRIVER=dummy` (main.py го задава автоматично).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from engine.game import Game
from engine.states import PlayingState

# Клавиши, от които smoke тестът избира на случаен принцип.
SMOKE_KEYS: list[tuple[int, str]] = [
    (pygame.K_UP, ""), (pygame.K_DOWN, ""), (pygame.K_LEFT, ""), (pygame.K_RIGHT, ""),
    (pygame.K_q, "q"), (pygame.K_e, "e"), (pygame.K_z, "z"), (pygame.K_c, "c"),
    (pygame.K_PERIOD, "."),
]


@dataclass
class SmokeReport:
    """Резултат от smoke теста."""

    steps: int
    games_started: int


def key_event(key: int, unicode: str = "") -> pygame.event.Event:
    """Създава синтетично KEYDOWN събитие."""
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=0)


def run_smoke(steps: int, seed: int = 0) -> SmokeReport:
    """Стартира играта и изпълнява `steps` случайни натискания.

    Args:
        steps: Брой симулирани натискания на клавиш.
        seed: Seed за избора на клавиши (за повторимост).

    Returns:
        Кратък отчет.
    """
    chooser = random.Random(seed)
    game = Game()
    games_started = 0
    for _ in range(steps):
        if not isinstance(game.state, PlayingState):
            # Във всеки не-игрови екран натискаме Enter (напр. "Нова игра").
            game.handle_event(key_event(pygame.K_RETURN, "\r"))
            games_started += isinstance(game.state, PlayingState)
            continue
        key, char = chooser.choice(SMOKE_KEYS)
        game.handle_event(key_event(key, char))
        game.render()
    pygame.quit()
    return SmokeReport(steps=steps, games_started=games_started)

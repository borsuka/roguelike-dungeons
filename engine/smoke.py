"""Headless smoke test: пуска истинската игра без прозорец и натиска случайни клавиши.

Целта е да се хване всяка грешка (exception) при реална комбинация от екрани и действия.
Трябва да се извиква със `SDL_VIDEODRIVER=dummy` (main.py го задава автоматично).
"""

from __future__ import annotations

import random
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pygame

import config
from engine.game import Game
from engine.states import GameOverState, HighScoresState, MainMenuState, State, VictoryState
from engine.world import World

# Клавиши, от които smoke тестът избира на случаен принцип (код, символ).
SMOKE_KEYS: list[tuple[int, str]] = [
    (pygame.K_UP, ""), (pygame.K_DOWN, ""), (pygame.K_LEFT, ""), (pygame.K_RIGHT, ""),
    (pygame.K_q, "q"), (pygame.K_e, "e"), (pygame.K_z, "z"), (pygame.K_c, "c"),
    (pygame.K_UP, ""), (pygame.K_DOWN, ""), (pygame.K_LEFT, ""), (pygame.K_RIGHT, ""),
    (pygame.K_PERIOD, "."), (pygame.K_PERIOD, ">"), (pygame.K_g, "g"),
    (pygame.K_i, "i"), (pygame.K_a, "a"), (pygame.K_b, "b"), (pygame.K_d, "D"),
    (pygame.K_RETURN, "\r"), (pygame.K_ESCAPE, "\x1b"), (pygame.K_v, "v"),
    (pygame.K_PAGEUP, ""),
]
# Екрани, в които smoke тестът просто натиска Enter (за да започне/продължи игра).
ENTER_STATES: tuple[type[State], ...] = (
    MainMenuState, GameOverState, VictoryState, HighScoresState,
)

@dataclass
class SmokeReport:
    """Резултат от smoke теста."""

    steps: int
    games_started: int
    max_floor: int


def key_event(key: int, unicode: str = "") -> pygame.event.Event:
    """Създава синтетично KEYDOWN събитие."""
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=0)


def current_world(state: State) -> World | None:
    """Светът, който екранът показва (ако има такъв)."""
    world = getattr(state, "world", None)
    if world is None and hasattr(state, "parent"):
        world = getattr(state.parent, "world", None)
    return world


def run_smoke(steps: int, seed: int = 0) -> SmokeReport:
    """Стартира играта и изпълнява `steps` случайни натискания.

    Args:
        steps: Брой симулирани натискания на клавиш.
        seed: Seed за избора на клавиши и за първата игра (за повторимост).

    Returns:
        Кратък отчет.
    """
    chooser = random.Random(seed)
    # Рекордите от теста отиват във временна папка, а не в истинската таблица.
    with tempfile.TemporaryDirectory() as tmp_dir:
        game = Game(seed=seed, highscore_path=Path(tmp_dir) / "highscores.json")
        report = _run_steps(game, chooser, steps)
    pygame.quit()
    return report


def _run_steps(game: Game, chooser: random.Random, steps: int) -> SmokeReport:
    """Основният цикъл на smoke теста."""
    games_started = 0
    max_floor = 0
    for _ in range(steps):
        if isinstance(game.state, ENTER_STATES):
            game.handle_event(key_event(pygame.K_RETURN, "\r"))
            games_started += current_world(game.state) is not None
            game.render()
            continue
        world = current_world(game.state)
        if world is not None and chooser.random() < config.SMOKE_DESCEND_CHANCE \
                and world.game_map.stairs is not None and world.player.is_alive:
            # Случайното ходене рядко стига до стълбите, затова понякога "телепортираме"
            # играча там – така тестът минава и през генерирането на нови етажи.
            world.player.place(*world.game_map.stairs)
            world.update_fov()
            key, char = pygame.K_PERIOD, ">"
        else:
            key, char = chooser.choice(SMOKE_KEYS)
        game.handle_event(key_event(key, char))
        game.render()
        game.running = True  # smoke тестът игнорира "Изход" от менюто за пауза
        if world is not None:
            max_floor = max(max_floor, world.floor)
    return SmokeReport(steps=steps, games_started=games_started, max_floor=max_floor)

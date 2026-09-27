"""Headless тестове: истинската игра с pygame, но без прозорец."""

from __future__ import annotations

import os
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402  (след задаване на env)

from engine.game import Game  # noqa: E402
from engine.smoke import key_event, run_smoke  # noqa: E402
from engine.states import (  # noqa: E402
    GameOverState,
    HighScoresState,
    InventoryState,
    LevelUpState,
    MainMenuState,
    MessageLogState,
    PauseState,
    PlayingState,
)
from ui.highscores import load_scores  # noqa: E402


def press(game: Game, key: int, char: str = "") -> None:
    game.handle_event(key_event(key, char))
    game.render()


def new_game(tmp_path: Path) -> Game:
    game = Game(seed=42, highscore_path=tmp_path / "hs.json")
    press(game, pygame.K_RETURN, "\r")
    assert isinstance(game.state, PlayingState)
    return game


def test_smoke_short_session() -> None:
    report = run_smoke(steps=200, seed=1)  # Definition of Done: 200 случайни хода
    assert report.games_started >= 1


def test_menu_navigation_and_highscores_screen(tmp_path: Path) -> None:
    game = Game(highscore_path=tmp_path / "hs.json")
    press(game, pygame.K_DOWN)
    press(game, pygame.K_RETURN, "\r")
    assert isinstance(game.state, HighScoresState)
    press(game, pygame.K_ESCAPE)
    assert isinstance(game.state, MainMenuState)


def test_pause_log_and_inventory_screens(tmp_path: Path) -> None:
    game = new_game(tmp_path)
    playing = game.state
    press(game, pygame.K_ESCAPE)
    assert isinstance(game.state, PauseState)
    press(game, pygame.K_ESCAPE)
    assert game.state is playing
    press(game, pygame.K_v, "v")
    assert isinstance(game.state, MessageLogState)
    press(game, pygame.K_UP)
    press(game, pygame.K_v, "v")
    assert game.state is playing
    press(game, pygame.K_i, "i")
    assert isinstance(game.state, InventoryState)
    press(game, pygame.K_ESCAPE)
    assert game.state is playing


def test_death_records_highscore(tmp_path: Path) -> None:
    game = new_game(tmp_path)
    world = game.state.world
    world.player.fighter.take_damage(1000)
    world.handle_death(world.player)
    game.state = game.state.next_state()
    assert isinstance(game.state, GameOverState)
    game.render()
    scores = load_scores(tmp_path / "hs.json")
    assert len(scores) == 1 and scores[0].seed == 42
    press(game, pygame.K_RETURN, "\r")
    assert isinstance(game.state, MainMenuState)


def test_level_up_screen_applies_choice(tmp_path: Path) -> None:
    game = new_game(tmp_path)
    world = game.state.world
    world.player.level.add_xp(world.player.level.experience_to_next_level)
    press(game, pygame.K_PERIOD, ".")
    assert isinstance(game.state, LevelUpState)
    attack = world.player.fighter.attack
    press(game, pygame.K_b, "b")
    assert world.player.fighter.attack == attack + 1
    assert isinstance(game.state, PlayingState)

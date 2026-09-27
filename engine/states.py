"""Екрани на играта (State pattern).

Всеки екран е отделен клас с два метода:
- `handle_event(event)` – реагира на вход и може да върне нов State (преход);
- `render(renderer)` – рисува себе си.
Така `Game` не съдържа нито един `if` за "в кой екран сме".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from engine.actions import Action
from engine.input_handler import Command, key_name, translate_key
from engine.renderer import Renderer
from engine.world import World

if TYPE_CHECKING:
    from engine.game import Game


class State:
    """Базов клас за екран.

    Attributes:
        game: Главният обект на играта (за достъп до настройки и изход).
    """

    def __init__(self, game: Game) -> None:
        self.game = game

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Обработва събитие. Връща нов State при преход, иначе None."""
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува екрана."""


class MenuState(State):
    """Общ екран с вертикален списък от опции, избирани със стрелки и Enter."""

    title = ""
    options: list[str] = []

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.selected = 0

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Стрелки мести избора, Enter го потвърждава."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        if name in config.MENU_UP_KEYS:
            self.selected = (self.selected - 1) % len(self.options)
        elif name in config.MENU_DOWN_KEYS:
            self.selected = (self.selected + 1) % len(self.options)
        elif name in config.CONFIRM_KEYS:
            return self.on_select(self.selected)
        elif name == config.ESCAPE_KEY:
            return self.on_cancel()
        return None

    def on_select(self, index: int) -> State | None:
        """Извиква се при избор на опция."""
        return None

    def on_cancel(self) -> State | None:
        """Извиква се при Esc."""
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува заглавие и опции в центъра на екрана."""
        renderer.screen.fill(config.COLOR_BLACK)
        center_x = config.SCREEN_WIDTH // 2
        renderer.draw_text(self.title, (center_x, config.SCREEN_HEIGHT // 4),
                           config.COLOR_TITLE, renderer.title_font, center=True)
        for i, option in enumerate(self.options):
            selected = i == self.selected
            color = config.COLOR_MENU_SELECTED if selected else config.COLOR_MENU_TEXT
            text = f"> {option} <" if selected else option
            y = config.SCREEN_HEIGHT // 2 + i * (config.FONT_SIZE_MENU + 12)
            renderer.draw_text(text, (center_x, y), color, renderer.menu_font, center=True)


class MainMenuState(MenuState):
    """Главно меню."""

    title = "ПОДЗЕМИЯТА НА КРАЛЯ"
    options = ["Нова игра", "Изход"]

    def on_select(self, index: int) -> State | None:
        """Стартира нова игра или затваря програмата."""
        if index == 0:
            return PlayingState(self.game, World.new_test_world())
        self.game.running = False
        return None

    def on_cancel(self) -> State | None:
        """Esc в главното меню затваря играта."""
        self.game.running = False
        return None


class PlayingState(State):
    """Самата игра: карта, играч, ходове."""

    def __init__(self, game: Game, world: World) -> None:
        super().__init__(game)
        self.world = world

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Превежда клавиша в действие и го изпълнява."""
        if event.type != pygame.KEYDOWN:
            return None
        result = translate_key(event, self.world.player)
        if result is Command.PAUSE:
            return MainMenuState(self.game)
        if isinstance(result, Action):
            result.perform(self.world)
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува света."""
        renderer.screen.fill(config.COLOR_BLACK)
        renderer.draw_world(self.world)

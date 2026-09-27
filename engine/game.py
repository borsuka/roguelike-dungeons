"""Основният цикъл на играта и управлението на екраните (state machine)."""

from __future__ import annotations

from pathlib import Path

import pygame

import config
from engine.renderer import Renderer
from engine.states import MainMenuState, State


class Game:
    """Притежава прозореца, часовника и текущия екран (State).

    Attributes:
        running: Докато е True, основният цикъл продължава.
        state: Текущият екран.
    """

    def __init__(self, seed: int | None = None,
                 highscore_path: Path = config.HIGHSCORE_PATH) -> None:
        pygame.init()
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.running = True
        self.highscore_path = highscore_path
        self._pending_seed = seed
        self.state: State = MainMenuState(self)

    def take_seed(self) -> int | None:
        """Seed за следващата нова игра.

        Seed-ът от `--seed` важи само за първата игра; следващите игри (след смърт) са с
        нови случайни карти – така работи permadeath.
        """
        seed, self._pending_seed = self._pending_seed, None
        return seed

    def handle_event(self, event: pygame.event.Event) -> None:
        """Предава събитието на текущия екран и сменя екрана при нужда."""
        if event.type == pygame.QUIT:
            self.running = False
            return
        new_state = self.state.handle_event(event)
        if new_state is not None:
            self.state = new_state

    def render(self) -> None:
        """Рисува текущия екран и обновява дисплея."""
        self.state.render(self.renderer)
        pygame.display.flip()

    def run(self) -> None:
        """Основен цикъл: събития → рисуване → изчакване до следващия кадър (60 FPS)."""
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.render()
            self.clock.tick(config.FPS)
        pygame.quit()

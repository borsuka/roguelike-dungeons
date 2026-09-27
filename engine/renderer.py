"""Рисуване на картата и обектите с pygame."""

from __future__ import annotations

import pygame

import config
from config import Color
from engine.world import World


class Renderer:
    """Рисува света върху pygame повърхност.

    Символите се рендерират веднъж и се кешират по (символ, цвят), защото
    `font.render` е скъпа операция, а едни и същи символи се рисуват всеки кадър.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.tile_font = pygame.font.Font(None, config.FONT_SIZE_TILE)
        self.ui_font = pygame.font.Font(None, config.FONT_SIZE_UI)
        self.menu_font = pygame.font.Font(None, config.FONT_SIZE_MENU)
        self.title_font = pygame.font.Font(None, config.FONT_SIZE_TITLE)
        self._glyph_cache: dict[tuple[str, Color], pygame.Surface] = {}

    # ------------------------------------------------------------------ помощни
    def glyph(self, char: str, color: Color) -> pygame.Surface:
        """Връща (кеширана) повърхност със символа."""
        key = (char, color)
        if key not in self._glyph_cache:
            self._glyph_cache[key] = self.tile_font.render(char, True, color)
        return self._glyph_cache[key]

    def draw_cell(self, screen_x: int, screen_y: int, char: str, fg: Color, bg: Color) -> None:
        """Рисува една клетка: цветен квадрат + центриран символ."""
        size = config.TILE_SIZE
        rect = pygame.Rect(screen_x * size, screen_y * size, size, size)
        pygame.draw.rect(self.screen, bg, rect)
        if char != " ":
            surface = self.glyph(char, fg)
            self.screen.blit(surface, surface.get_rect(center=rect.center))

    def draw_text(
        self, text: str, pos: tuple[int, int], color: Color, font: pygame.font.Font | None = None,
        center: bool = False,
    ) -> None:
        """Рисува текст на пикселна позиция (горе-ляво или център)."""
        surface = (font or self.ui_font).render(text, True, color)
        rect = surface.get_rect(center=pos) if center else surface.get_rect(topleft=pos)
        self.screen.blit(surface, rect)

    # ------------------------------------------------------------------ свят
    def draw_world(self, world: World) -> None:
        """Рисува картата и обектите."""
        game_map = world.game_map
        for x in range(min(game_map.width, config.VIEW_WIDTH_TILES)):
            for y in range(min(game_map.height, config.VIEW_HEIGHT_TILES)):
                t = game_map.tiles[x][y]
                self.draw_cell(x, y, t.char, t.light_fg, t.light_bg)
        for entity in sorted(game_map.entities, key=lambda e: e.render_order):
            t = game_map.tiles[entity.x][entity.y]
            self.draw_cell(entity.x, entity.y, entity.char, entity.color, t.light_bg)

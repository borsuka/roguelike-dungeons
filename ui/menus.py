"""Рисуване на прозорци с менюта върху играта."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from config import Color

if TYPE_CHECKING:
    from engine.renderer import Renderer


def draw_menu_box(renderer: Renderer, title: str, lines: list[tuple[str, Color]],
                  footer: str = "", width: int = config.MENU_BOX_WIDTH) -> None:
    """Центриран полупрозрачен прозорец със заглавие, редове и подсказка отдолу.

    Args:
        renderer: Рендерерът.
        title: Заглавие.
        lines: Редове (текст, цвят).
        footer: Подсказка за клавишите.
        width: Ширина на прозореца в пиксели.
    """
    font = renderer.ui_font
    line_h = font.get_linesize() + 4
    pad = config.PANEL_PADDING * 2
    body_lines = max(1, len(lines))
    height = pad * 2 + line_h * (body_lines + 2) + (line_h if footer else 0)
    rect = pygame.Rect(0, 0, width, height)
    rect.center = (config.SCREEN_WIDTH // 2, (config.SCREEN_HEIGHT - config.PANEL_HEIGHT) // 2)

    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
    overlay.fill((*config.COLOR_MENU_BOX_BG, 235))
    renderer.screen.blit(overlay, rect.topleft)
    pygame.draw.rect(renderer.screen, config.COLOR_PANEL_BORDER, rect, width=2)

    renderer.draw_text(title, (rect.centerx, rect.top + pad + line_h // 2),
                       config.COLOR_TITLE, renderer.menu_font, center=True)
    y = rect.top + pad + line_h * 2
    if not lines:
        renderer.draw_text("(празно)", (rect.left + pad, y), config.COLOR_GRAY)
    for text, color in lines:
        renderer.draw_text(text, (rect.left + pad, y), color)
        y += line_h
    if footer:
        renderer.draw_text(footer, (rect.centerx, rect.bottom - pad - line_h // 2),
                           config.COLOR_GRAY, center=True)

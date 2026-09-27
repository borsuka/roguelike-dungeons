"""HUD: долният панел със статистики и последните съобщения."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from config import Color

if TYPE_CHECKING:
    from engine.renderer import Renderer
    from engine.world import World
    from ui.message_log import MessageLog


def draw_bar(surface: pygame.Surface, rect: pygame.Rect, value: int, maximum: int,
             full: Color, empty: Color) -> None:
    """Хоризонтална лента (напр. HP): запълнената част е пропорционална на value/maximum."""
    pygame.draw.rect(surface, empty, rect)
    if maximum > 0 and value > 0:
        filled = rect.copy()
        filled.width = int(rect.width * min(value, maximum) / maximum)
        pygame.draw.rect(surface, full, filled)


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Разделя текста на редове, които се събират в `max_width` пиксела."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_messages(renderer: Renderer, log: MessageLog, rect: pygame.Rect) -> None:
    """Рисува последните съобщения отдолу нагоре, докато има място в `rect`."""
    font = renderer.ui_font
    line_height = font.get_linesize()
    y = rect.bottom - line_height
    for message in reversed(log.last(config.LOG_PANEL_LINES)):
        for line in reversed(wrap_text(message.full_text, font, rect.width)):
            if y < rect.top:
                return
            renderer.screen.blit(font.render(line, True, message.color), (rect.left, y))
            y -= line_height


def draw_hud(renderer: Renderer, world: World) -> None:
    """Рисува целия долен панел."""
    screen = renderer.screen
    pad = config.PANEL_PADDING
    top = config.SCREEN_HEIGHT - config.PANEL_HEIGHT
    pygame.draw.rect(screen, config.COLOR_PANEL_BG,
                     (0, top, config.SCREEN_WIDTH, config.PANEL_HEIGHT))
    pygame.draw.line(screen, config.COLOR_PANEL_BORDER, (0, top), (config.SCREEN_WIDTH, top))

    fighter = world.player.fighter
    bar = pygame.Rect(pad, top + pad, config.HUD_WIDTH - 2 * pad, config.BAR_HEIGHT)
    draw_bar(screen, bar, fighter.hp, fighter.max_hp,
             config.COLOR_HP_BAR_FULL, config.COLOR_HP_BAR_EMPTY)
    renderer.draw_text(f"HP: {fighter.hp}/{fighter.max_hp}", (bar.x + 4, bar.y),
                       config.COLOR_WHITE)
    line = renderer.ui_font.get_linesize()
    level = world.player.level
    if level is not None:
        xp_bar = pygame.Rect(pad, bar.bottom + 4, bar.width, config.BAR_HEIGHT)
        draw_bar(screen, xp_bar, level.current_xp, level.experience_to_next_level,
                 config.COLOR_XP_BAR_FULL, config.COLOR_XP_BAR_EMPTY)
        renderer.draw_text(
            f"Ниво {level.current_level}   XP: {level.current_xp}/{level.experience_to_next_level}",
            (xp_bar.x + 4, xp_bar.y), config.COLOR_WHITE)
        bar = xp_bar
    info = [
        f"Етаж: {world.floor}    Ход: {world.turn}    Убити: {world.kills}",
        f"Атака: {fighter.attack}    Защита: {fighter.defense}",
        f"Seed: {world.seed}",
    ]
    for i, text in enumerate(info):
        renderer.draw_text(text, (pad, bar.bottom + 4 + i * line), config.COLOR_MENU_TEXT)

    log_rect = pygame.Rect(config.HUD_WIDTH, top + pad,
                           config.SCREEN_WIDTH - config.HUD_WIDTH - pad,
                           config.PANEL_HEIGHT - 2 * pad)
    pygame.draw.line(screen, config.COLOR_PANEL_BORDER, (config.HUD_WIDTH - pad, top),
                     (config.HUD_WIDTH - pad, config.SCREEN_HEIGHT))
    draw_messages(renderer, world.message_log, log_rect)

"""Типове тайлове (клетки на картата)."""

from __future__ import annotations

from dataclasses import dataclass

import config
from config import Color


@dataclass(frozen=True)
class TileType:
    """Неизменим тип тайл.

    Всички клетки от един тип сочат към един и същ обект, затова картата пази само
    референции – няма копие на данните за всяка клетка.

    Attributes:
        name: Име за дебъг/тестове.
        walkable: Може ли да се стъпва върху тайла.
        transparent: Пропуска ли светлина (важно за FOV).
        char: Символ, с който се рисува.
        light_fg: Цвят на символа, когато е видим.
        light_bg: Цвят на фона, когато е видим.
        dark_fg: Цвят на символа, когато е изследван, но не се вижда в момента.
        dark_bg: Цвят на фона, когато е изследван, но не се вижда в момента.
    """

    name: str
    walkable: bool
    transparent: bool
    char: str
    light_fg: Color
    light_bg: Color
    dark_fg: Color
    dark_bg: Color


WALL = TileType(
    name="wall", walkable=False, transparent=False, char="#",
    light_fg=config.COLOR_WALL_LIGHT_FG, light_bg=config.COLOR_WALL_LIGHT_BG,
    dark_fg=config.COLOR_WALL_DARK_FG, dark_bg=config.COLOR_WALL_DARK_BG,
)

FLOOR = TileType(
    name="floor", walkable=True, transparent=True, char=".",
    light_fg=config.COLOR_FLOOR_LIGHT_FG, light_bg=config.COLOR_FLOOR_LIGHT_BG,
    dark_fg=config.COLOR_FLOOR_DARK_FG, dark_bg=config.COLOR_FLOOR_DARK_BG,
)

STAIRS_DOWN = TileType(
    name="stairs_down", walkable=True, transparent=True, char=">",
    light_fg=config.COLOR_STAIRS_LIGHT_FG, light_bg=config.COLOR_FLOOR_LIGHT_BG,
    dark_fg=config.COLOR_STAIRS_DARK_FG, dark_bg=config.COLOR_FLOOR_DARK_BG,
)

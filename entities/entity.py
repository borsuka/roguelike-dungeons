"""Базов клас за всичко, което има позиция на картата."""

from __future__ import annotations

from enum import IntEnum

from config import Color


class RenderOrder(IntEnum):
    """Ред на рисуване: по-голямата стойност се рисува най-отгоре."""

    CORPSE = 0
    ITEM = 1
    ACTOR = 2


class Entity:
    """Обект в света: играч, враг, предмет, труп.

    Attributes:
        x: Колона на картата.
        y: Ред на картата.
        char: Символ за рисуване.
        color: Цвят на символа.
        name: Име, което се показва в съобщенията.
        blocks_movement: Дали други не могат да влязат в клетката му.
        render_order: Приоритет при рисуване.
    """

    def __init__(
        self,
        x: int,
        y: int,
        char: str,
        color: Color,
        name: str,
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
    ) -> None:
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order

    @property
    def position(self) -> tuple[int, int]:
        """Текущата позиция като (x, y)."""
        return self.x, self.y

    def move(self, dx: int, dy: int) -> None:
        """Премества обекта с (dx, dy), без проверки – те са отговорност на действията."""
        self.x += dx
        self.y += dy

    def place(self, x: int, y: int) -> None:
        """Поставя обекта директно на (x, y)."""
        self.x = x
        self.y = y

    def distance_to(self, x: int, y: int) -> int:
        """Chebyshev разстояние (брой ходове при 8-посочно движение) до (x, y)."""
        return max(abs(self.x - x), abs(self.y - y))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r} @ {self.x},{self.y})"

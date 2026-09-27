"""Камера: коя част от картата се вижда на екрана (без pygame)."""

from __future__ import annotations


class Camera:
    """Следи играча и превежда координати от картата към екрана.

    Камерата се центрира върху целта, но не излиза извън картата – така по ръбовете
    играчът не е в центъра, но никога не виждаме празно пространство отвъд картата.

    Attributes:
        x: Колоната на картата, показана в левия край на екрана.
        y: Редът на картата, показан в горния край на екрана.
    """

    def __init__(self, view_width: int, view_height: int, map_width: int, map_height: int) -> None:
        self.view_width = view_width
        self.view_height = view_height
        self.map_width = map_width
        self.map_height = map_height
        self.x = 0
        self.y = 0

    def center_on(self, target_x: int, target_y: int) -> None:
        """Центрира камерата върху (target_x, target_y), ограничено в картата."""
        self.x = _clamp(target_x - self.view_width // 2, 0,
                        max(0, self.map_width - self.view_width))
        self.y = _clamp(target_y - self.view_height // 2, 0,
                        max(0, self.map_height - self.view_height))

    def to_screen(self, map_x: int, map_y: int) -> tuple[int, int]:
        """Координати на картата → координати на екрана (в тайлове)."""
        return map_x - self.x, map_y - self.y

    def to_map(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        """Координати на екрана (в тайлове) → координати на картата."""
        return screen_x + self.x, screen_y + self.y

    def is_on_screen(self, map_x: int, map_y: int) -> bool:
        """Дали клетката от картата попада в изгледа."""
        sx, sy = self.to_screen(map_x, map_y)
        return 0 <= sx < self.view_width and 0 <= sy < self.view_height


def _clamp(value: int, low: int, high: int) -> int:
    """Ограничава стойността в [low, high]."""
    return max(low, min(high, value))

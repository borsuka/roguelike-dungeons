"""Картата на един етаж: тайлове и обекти върху тях."""

from __future__ import annotations

from collections.abc import Iterator

from entities.entity import Entity
from world import fov, tile
from world.generators.base import GenerationResult, Rect
from world.tile import TileType


class GameMap:
    """Мрежа от тайлове плюс списък с обектите на етажа.

    Тайловете се пазят като `tiles[x][y]` (първо колона, после ред), за да съвпада
    с математическия запис (x, y).

    Attributes:
        width: Ширина в тайлове.
        height: Височина в тайлове.
        tiles: 2D масив от TileType.
        entities: Всички обекти на етажа (включително играча).
        visible: [x][y] – вижда ли се клетката в момента.
        explored: [x][y] – виждана ли е клетката някога.
    """

    def __init__(self, width: int, height: int, fill: TileType = tile.WALL) -> None:
        self.width = width
        self.height = height
        self.tiles: list[list[TileType]] = [[fill] * height for _ in range(width)]
        self.entities: list[Entity] = []
        self.visible: list[list[bool]] = [[False] * height for _ in range(width)]
        self.explored: list[list[bool]] = [[False] * height for _ in range(width)]
        self.rooms: list[Rect] = []
        self.player_start: tuple[int, int] = (width // 2, height // 2)
        self.stairs: tuple[int, int] | None = None
        self.start_area: set[tuple[int, int]] = set()

    @classmethod
    def from_generation(cls, result: GenerationResult) -> GameMap:
        """Създава карта от резултата на генератор."""
        game_map = cls(result.width, result.height)
        game_map.tiles = [list(column) for column in result.tiles]
        game_map.rooms = list(result.rooms)
        game_map.player_start = result.player_start
        game_map.stairs = result.stairs
        game_map.start_area = set(result.start_area)
        return game_map

    # ------------------------------------------------------------------ тайлове
    def in_bounds(self, x: int, y: int) -> bool:
        """Връща True, ако (x, y) е в границите на картата."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        """Може ли да се стъпи на (x, y) според тайла (без да гледаме обекти)."""
        return self.in_bounds(x, y) and self.tiles[x][y].walkable

    def is_transparent(self, x: int, y: int) -> bool:
        """Пропуска ли тайлът на (x, y) светлина."""
        return self.in_bounds(x, y) and self.tiles[x][y].transparent

    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        """Задава тип на тайла на (x, y)."""
        self.tiles[x][y] = tile_type

    def update_fov(self, origin: tuple[int, int], radius: int) -> None:
        """Преизчислява `visible` от `origin`; видяното се добавя към `explored`."""
        self.visible = [[False] * self.height for _ in range(self.width)]
        for x, y in fov.compute_fov(self.transparent_grid(), origin, radius):
            self.visible[x][y] = True
            self.explored[x][y] = True

    def is_visible(self, x: int, y: int) -> bool:
        """Вижда ли се клетката (x, y) в момента."""
        return self.in_bounds(x, y) and self.visible[x][y]

    def walkable_grid(self) -> list[list[bool]]:
        """2D масив [x][y] с проходимостта – вход за BFS и A*."""
        return [[t.walkable for t in column] for column in self.tiles]

    def transparent_grid(self) -> list[list[bool]]:
        """2D масив [x][y] с прозрачността – вход за FOV."""
        return [[t.transparent for t in column] for column in self.tiles]

    # ------------------------------------------------------------------ обекти
    def add_entity(self, entity: Entity) -> None:
        """Добавя обект на етажа."""
        self.entities.append(entity)

    def remove_entity(self, entity: Entity) -> None:
        """Премахва обект от етажа (ако го има)."""
        if entity in self.entities:
            self.entities.remove(entity)

    def entities_at(self, x: int, y: int) -> Iterator[Entity]:
        """Всички обекти на (x, y)."""
        return (e for e in self.entities if e.x == x and e.y == y)

    def get_blocking_entity_at(self, x: int, y: int) -> Entity | None:
        """Обектът, който блокира движение на (x, y), или None."""
        for entity in self.entities:
            if entity.blocks_movement and entity.x == x and entity.y == y:
                return entity
        return None

    def is_free(self, x: int, y: int) -> bool:
        """Проходим тайл и без блокиращ обект."""
        return self.is_walkable(x, y) and self.get_blocking_entity_at(x, y) is None

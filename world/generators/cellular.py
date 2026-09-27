"""Cellular Automata генератор на пещери.

Идея (като "Играта на живота" на Конуей, но с друго правило):
1. Запълваме картата на случаен принцип: ~45% стени, рамката винаги е стена.
2. Няколко пъти прилагаме правило, което гледа 3x3 околността на всяка клетка:
   много стени наоколо → стена; малко → под. Шумът се "изглажда" в естествени пещери.
3. Остават несвързани джобове – пазим само най-големия регион, другите запълваме.
4. Ако регионът е твърде малък, генерираме отново с нов под-seed.
"""

from __future__ import annotations

import config
from systems import rng as rng_module
from world import connectivity, tile
from world.generators.base import DungeonGenerator, Point, Rect, TileGrid

BoolGrid = list[list[bool]]


class CellularGenerator(DungeonGenerator):
    """Генератор на пещери чрез клетъчен автомат."""

    def _carve(self) -> tuple[TileGrid, list[Rect]]:
        """Генерира пещера; при твърде малък регион опитва отново с нов под-seed."""
        min_floor = config.CA_MIN_FLOOR_RATIO * self.width * self.height
        for _ in range(config.CA_MAX_ATTEMPTS):
            walls = self._random_fill()
            for iteration in range(config.CA_ITERATIONS):
                walls = self._step(walls, fill_empty=iteration < config.CA_EMPTY_FILL_ITERATIONS)
            floor = [[not cell for cell in column] for column in walls]
            regions = connectivity.find_regions(floor)
            if regions and len(regions[0]) >= min_floor:
                return self._tiles_from_region(regions[0]), []
            # Нов под-seed, изведен от текущия генератор → пак детерминистично.
            self.rng = rng_module.make_rng(self.rng.randrange(config.SEED_MAX))
        raise RuntimeError("Неуспешно генериране на пещера")

    # ------------------------------------------------------------------ стъпки
    def is_border(self, x: int, y: int) -> bool:
        """Дали клетката е на рамката на картата."""
        return x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1

    def _random_fill(self) -> BoolGrid:
        """Начално попълване: True = стена."""
        return [
            [self.is_border(x, y) or self.rng.random() < config.CA_WALL_PROBABILITY
             for y in range(self.height)]
            for x in range(self.width)
        ]

    def count_walls(self, walls: BoolGrid, x: int, y: int) -> int:
        """Брой стени в 3x3 околността на (x, y), включително самата клетка.

        Клетките извън картата се броят за стени – така ръбовете "привличат" стени.
        """
        count = 0
        for nx in range(x - 1, x + 2):
            for ny in range(y - 1, y + 2):
                outside = not (0 <= nx < self.width and 0 <= ny < self.height)
                if outside or walls[nx][ny]:
                    count += 1
        return count

    def _step(self, walls: BoolGrid, fill_empty: bool) -> BoolGrid:
        """Една итерация на правилото.

        Стена, ако в 3x3 има ≥ 5 стени. В първите итерации също и ако има 0 стени –
        това "засажда" колони в големи празни зали, за да не стават огромни поляни.
        Новото състояние се смята в НОВ масив, за да не влияе на съседите в същата итерация.
        """
        new_walls: BoolGrid = [[True] * self.height for _ in range(self.width)]
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                n = self.count_walls(walls, x, y)
                new_walls[x][y] = n >= config.CA_WALL_THRESHOLD or (fill_empty and n == 0)
        return new_walls

    def _tiles_from_region(self, region: set[Point]) -> TileGrid:
        """Под само в клетките на региона, навсякъде другаде – стена."""
        tiles = self.new_grid(tile.WALL)
        for x, y in region:
            tiles[x][y] = tile.FLOOR
        return tiles

    # ------------------------------------------------------------------ старт
    def _choose_start(self, tiles: TileGrid, rooms: list[Rect]) -> Point:
        """Случайна подова клетка (сортираме за детерминизъм)."""
        floor_cells = sorted(
            (x, y) for x in range(self.width) for y in range(self.height) if tiles[x][y].walkable
        )
        return self.rng.choice(floor_cells)

    def _start_area(self, start: Point, rooms: list[Rect]) -> set[Point]:
        """Квадрат с радиус CA_SAFE_RADIUS около старта – без врагове."""
        sx, sy = start
        radius = config.CA_SAFE_RADIUS
        return {(x, y) for x in range(sx - radius, sx + radius + 1)
                for y in range(sy - radius, sy + radius + 1)}

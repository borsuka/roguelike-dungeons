"""Field of View чрез recursive shadowcasting и права линия на видимост (Bresenham).

Shadowcasting (алгоритъм на Björn Bergström):
- Около играча има 8 октанта (по 45°). Всеки се обработва с една и съща функция, като
  координатите се "завъртат" с 4 множителя (xx, xy, yx, yy).
- В октанта сканираме ред по ред навън от играча. Видимата част е "клин" между два
  наклона (start_slope и end_slope).
- Когато срещнем стена, клинът се разделя: за частта преди стената продължаваме
  рекурсивно на следващия ред, а след стената стесняваме клина. Така стените хвърлят
  "сянка" и клетките зад тях не се виждат.
Всяка клетка в радиуса се посещава най-много веднъж на октант → O(r²).
"""

from __future__ import annotations

Grid = list[list[bool]]
Point = tuple[int, int]

# Множители (xx, xy, yx, yy) за 8-те октанта.
OCTANTS: tuple[tuple[int, int, int, int], ...] = (
    (1, 0, 0, 1), (0, 1, 1, 0), (0, -1, 1, 0), (-1, 0, 0, 1),
    (-1, 0, 0, -1), (0, -1, -1, 0), (0, 1, -1, 0), (1, 0, 0, -1),
)


def compute_fov(transparent: Grid, origin: Point, radius: int) -> set[Point]:
    """Изчислява видимите клетки от `origin`.

    Args:
        transparent: 2D масив [x][y] – True, ако клетката пропуска светлина.
        origin: Позицията на наблюдателя.
        radius: Радиус на видимост (Евклидов).

    Returns:
        Множество от видими клетки (включително самата `origin` и осветените стени).
    """
    visible = {origin}
    for octant in OCTANTS:
        _cast_light(transparent, origin, radius, 1, 1.0, 0.0, octant, visible)
    return visible


def _cast_light(
    transparent: Grid, origin: Point, radius: int, row: int,
    start_slope: float, end_slope: float,
    octant: tuple[int, int, int, int], visible: set[Point],
) -> None:
    """Осветява един октант от ред `row` навън, между наклоните start и end."""
    if start_slope < end_slope:
        return
    width, height = len(transparent), len(transparent[0])
    ox, oy = origin
    xx, xy, yx, yy = octant
    radius_sq = radius * radius
    new_start = start_slope
    for distance in range(row, radius + 1):
        blocked = False
        dy = -distance
        for dx in range(-distance, 1):
            map_x = ox + dx * xx + dy * xy
            map_y = oy + dx * yx + dy * yy
            # Наклоните на левия и десния ръб на клетката (гледано от наблюдателя).
            left_slope = (dx - 0.5) / (dy + 0.5)
            right_slope = (dx + 0.5) / (dy - 0.5)
            if start_slope < right_slope:
                continue  # клетката е вляво от клина
            if end_slope > left_slope:
                break  # клетката (и всички след нея) са вдясно от клина
            inside = 0 <= map_x < width and 0 <= map_y < height
            if inside and dx * dx + dy * dy <= radius_sq:
                visible.add((map_x, map_y))
            opaque = not inside or not transparent[map_x][map_y]
            if blocked:
                if opaque:
                    new_start = right_slope  # продължава поредица от стени
                    continue
                blocked = False  # стената свърши – клинът започва от ръба ѝ
                start_slope = new_start
            elif opaque and distance < radius:
                # Начало на стена: частта преди нея продължава рекурсивно.
                blocked = True
                _cast_light(transparent, origin, radius, distance + 1,
                            start_slope, left_slope, octant, visible)
                new_start = right_slope
        if blocked:
            break  # целият остатък от реда е в сянка


def bresenham_line(start: Point, end: Point) -> list[Point]:
    """Клетките по права линия от `start` до `end` (включително двата края)."""
    (x0, y0), (x1, y1) = start, end
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    points = []
    while True:
        points.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return points
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def has_line_of_sight(transparent: Grid, start: Point, end: Point) -> bool:
    """True, ако никоя клетка МЕЖДУ `start` и `end` не блокира светлината."""
    return all(transparent[x][y] for x, y in bresenham_line(start, end)[1:-1])

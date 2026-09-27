"""Тестове за BFS / flood fill / региони."""

from __future__ import annotations

from tests.helpers import grid_from
from world import connectivity


TWO_ROOMS = [
    "#######",
    "#..#..#",
    "#..#..#",
    "#######",
]


def test_flood_fill_stays_in_region() -> None:
    grid = grid_from(TWO_ROOMS)
    assert connectivity.flood_fill(grid, (1, 1)) == {(1, 1), (2, 1), (1, 2), (2, 2)}


def test_flood_fill_from_wall_is_empty() -> None:
    assert connectivity.flood_fill(grid_from(TWO_ROOMS), (0, 0)) == set()


def test_find_regions_counts_separate_areas() -> None:
    regions = connectivity.find_regions(grid_from(TWO_ROOMS))
    assert len(regions) == 2
    assert all(len(region) == 4 for region in regions)


def test_regions_sorted_largest_first() -> None:
    rows = [
        "########",
        "#.#....#",
        "########",
    ]
    regions = connectivity.find_regions(grid_from(rows))
    assert [len(r) for r in regions] == [4, 1]


def test_diagonal_is_not_connected() -> None:
    # 4-посочна свързаност: клетките по диагонал НЕ са свързани.
    rows = [
        "####",
        "#.##",
        "##.#",
        "####",
    ]
    assert len(connectivity.find_regions(grid_from(rows))) == 2


def test_bfs_distances_are_shortest() -> None:
    rows = [
        "######",
        "#....#",
        "#.##.#",
        "#....#",
        "######",
    ]
    distances = connectivity.bfs_distances(grid_from(rows), (1, 1))
    assert distances[(1, 1)] == 0
    assert distances[(4, 1)] == 3
    assert distances[(4, 3)] == 5


def test_all_reachable_and_farthest_point() -> None:
    grid = grid_from(TWO_ROOMS)
    assert connectivity.all_reachable(grid, (1, 1), [(2, 2)])
    assert not connectivity.all_reachable(grid, (1, 1), [(4, 1)])
    assert connectivity.farthest_point(grid, (1, 1)) == (2, 2)

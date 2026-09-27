"""Тестове за камерата."""

from __future__ import annotations

from engine.camera import Camera


def test_camera_centers_on_target() -> None:
    camera = Camera(10, 6, 100, 50)
    camera.center_on(50, 25)
    assert (camera.x, camera.y) == (45, 22)
    assert camera.to_screen(50, 25) == (5, 3)


def test_camera_is_clamped_to_map_edges() -> None:
    camera = Camera(10, 6, 100, 50)
    camera.center_on(0, 0)
    assert (camera.x, camera.y) == (0, 0)
    camera.center_on(99, 49)
    assert (camera.x, camera.y) == (90, 44)


def test_camera_on_small_map_stays_at_origin() -> None:
    camera = Camera(40, 18, 20, 10)
    camera.center_on(15, 8)
    assert (camera.x, camera.y) == (0, 0)


def test_to_map_is_inverse_of_to_screen() -> None:
    camera = Camera(10, 6, 100, 50)
    camera.center_on(30, 30)
    assert camera.to_map(*camera.to_screen(33, 31)) == (33, 31)
    assert camera.is_on_screen(30, 30)
    assert not camera.is_on_screen(0, 0)

"""Headless smoke test: истинската игра с pygame, но без прозорец."""

from __future__ import annotations

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from engine.smoke import run_smoke  # noqa: E402  (след задаване на env)


def test_smoke_short_session() -> None:
    report = run_smoke(steps=60, seed=1)
    assert report.games_started >= 1

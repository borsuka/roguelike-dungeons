"""Тестове за таблицата с рекорди (Етап 8)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import config
from ui.highscores import (
    ScoreEntry,
    add_score,
    calculate_score,
    load_scores,
    make_entry,
    save_scores,
)


def entry(score_floor: int, kills: int = 0, turns: int = 100, victory: bool = False) -> ScoreEntry:
    return make_entry(floor=score_floor, kills=kills, turns=turns, level=1, victory=victory,
                      seed=1)


def test_score_formula() -> None:
    assert calculate_score(floor=3, kills=5, level=2, victory=False) == \
        3 * config.SCORE_PER_FLOOR + 5 * config.SCORE_PER_KILL + config.SCORE_PER_LEVEL
    assert calculate_score(10, 0, 1, True) - calculate_score(10, 0, 1, False) == \
        config.SCORE_VICTORY_BONUS


def test_missing_file_gives_empty_list(tmp_path: Path) -> None:
    assert load_scores(tmp_path / "няма.json") == []


@pytest.mark.parametrize("content", [
    "{not json",
    "",
    '{"score": 5}',            # обект вместо списък
    '"текст"',
    "\x00\x01\x02",
])
def test_corrupted_file_does_not_crash(tmp_path: Path, content: str) -> None:
    path = tmp_path / "highscores.json"
    path.write_text(content, encoding="utf-8")
    assert load_scores(path) == []
    # И след повреда може да се запише нов рекорд.
    assert add_score(path, entry(2)) == 1
    assert len(load_scores(path)) == 1


def test_invalid_entries_are_skipped(tmp_path: Path) -> None:
    good = {"score": 500, "floor": 5, "kills": 3, "turns": 200, "level": 2,
            "victory": False, "seed": 1, "date": "2026-01-01"}
    bad_type = dict(good, score="много")
    missing = {k: v for k, v in good.items() if k != "seed"}
    extra = dict(good, cheat=True)
    bool_as_int = dict(good, floor=True)
    path = tmp_path / "highscores.json"
    path.write_text(json.dumps([good, bad_type, missing, extra, bool_as_int, 42]),
                    encoding="utf-8")
    loaded = load_scores(path)
    assert len(loaded) == 1 and loaded[0].score == 500


def test_scores_persist_between_runs(tmp_path: Path) -> None:
    path = tmp_path / "highscores.json"
    add_score(path, entry(3))
    add_score(path, entry(7, victory=True))
    # "Ново стартиране": четем наново от диска.
    loaded = load_scores(path)
    assert [e.floor for e in loaded] == [7, 3]
    assert loaded[0].victory is True


def test_only_top_ten_are_kept(tmp_path: Path) -> None:
    path = tmp_path / "highscores.json"
    for floor in range(1, 15):
        add_score(path, entry(floor))
    loaded = load_scores(path)
    assert len(loaded) == config.HIGHSCORE_LIMIT
    assert loaded[0].floor == 14 and loaded[-1].floor == 5


def test_add_score_returns_rank_or_none(tmp_path: Path) -> None:
    path = tmp_path / "highscores.json"
    for floor in range(5, 15):
        add_score(path, entry(floor))
    assert add_score(path, entry(1)) is None       # твърде слаб за топ 10
    assert add_score(path, entry(20)) == 1         # нов първенец


def test_equal_scores_prefer_fewer_turns(tmp_path: Path) -> None:
    path = tmp_path / "highscores.json"
    save_scores(path, [entry(4, turns=500), entry(4, turns=100)])
    assert [e.turns for e in load_scores(path)] == [100, 500]


def test_saved_file_is_valid_utf8_json(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "highscores.json"
    add_score(path, entry(2))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list) and data[0]["floor"] == 2
    assert not list(path.parent.glob("*.tmp"))  # не остават временни файлове

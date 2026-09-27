"""Таблица с рекорди: четене и запис в JSON (без pygame).

Файлът може да липсва или да е повреден (ръчно редактиран, прекъснат запис) – тогава
просто започваме с празна таблица, вместо играта да се срине.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, fields
from datetime import date
from pathlib import Path

import config


@dataclass(frozen=True)
class ScoreEntry:
    """Един запис в таблицата.

    Attributes:
        score: Точки (виж `calculate_score`).
        floor: Най-дълбокият достигнат етаж.
        kills: Убити врагове.
        turns: Изиграни ходове.
        level: Ниво на играча.
        victory: Дали босът е победен.
        seed: Seed на играта (за повторение).
        date: Дата във формат ГГГГ-ММ-ДД.
    """

    score: int
    floor: int
    kills: int
    turns: int
    level: int
    victory: bool
    seed: int
    date: str


def calculate_score(floor: int, kills: int, level: int, victory: bool) -> int:
    """Точки = етаж·100 + убийства·10 + (ниво−1)·50 + бонус за победа."""
    score = floor * config.SCORE_PER_FLOOR + kills * config.SCORE_PER_KILL
    score += (level - 1) * config.SCORE_PER_LEVEL
    if victory:
        score += config.SCORE_VICTORY_BONUS
    return score


def make_entry(floor: int, kills: int, turns: int, level: int, victory: bool,
               seed: int) -> ScoreEntry:
    """Създава запис с изчислени точки и днешна дата."""
    return ScoreEntry(
        score=calculate_score(floor, kills, level, victory), floor=floor, kills=kills,
        turns=turns, level=level, victory=victory, seed=seed, date=date.today().isoformat(),
    )


def _entry_from_dict(raw: object) -> ScoreEntry | None:
    """Валидира един запис от JSON; връща None при грешни данни."""
    if not isinstance(raw, dict):
        return None
    expected = {f.name: f.type for f in fields(ScoreEntry)}
    if set(raw) != set(expected):
        return None
    for name, type_name in expected.items():
        value = raw[name]
        if type_name == "bool" and not isinstance(value, bool):
            return None
        if type_name == "int" and (not isinstance(value, int) or isinstance(value, bool)):
            return None
        if type_name == "str" and not isinstance(value, str):
            return None
    return ScoreEntry(**raw)


def load_scores(path: Path) -> list[ScoreEntry]:
    """Зарежда рекордите, сортирани по точки. Повреден/липсващ файл → празен списък."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    entries = [entry for entry in map(_entry_from_dict, data) if entry is not None]
    return sort_scores(entries)[: config.HIGHSCORE_LIMIT]


def sort_scores(entries: list[ScoreEntry]) -> list[ScoreEntry]:
    """По точки (намаляващо), при равенство – по-малко ходове е по-добре."""
    return sorted(entries, key=lambda e: (-e.score, e.turns))


def save_scores(path: Path, entries: list[ScoreEntry]) -> None:
    """Записва атомарно: първо във временен файл, после го преименува.

    Така прекъсване по време на запис не оставя полу-записан (повреден) файл.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps([asdict(e) for e in entries], ensure_ascii=False, indent=2)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(payload)
        os.replace(tmp_name, path)
    except OSError:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def add_score(path: Path, entry: ScoreEntry) -> int | None:
    """Добавя запис и пази само топ HIGHSCORE_LIMIT.

    Returns:
        Мястото в класацията (1 = първо) или None, ако не е влязъл в топа
        (или файлът не може да се запише).
    """
    entries = sort_scores(load_scores(path) + [entry])[: config.HIGHSCORE_LIMIT]
    try:
        save_scores(path, entries)
    except OSError:
        return None
    for index, existing in enumerate(entries):
        if existing is entry:
            return index + 1
    return None

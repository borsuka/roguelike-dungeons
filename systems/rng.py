"""Централизиран генератор на случайни числа.

Всичкият random в играта минава оттук. Една начална стойност (seed) определя цялата игра:
- картата на етаж N се генерира с `derive_seed(seed, "map", N)`, затова е една и съща
  при една и съща seed стойност – независимо какво е правил играчът преди това;
- боят и AI използват отделен `random.Random`, създаден от основния seed.
"""

from __future__ import annotations

import hashlib
import random

import config


def new_seed() -> int:
    """Нов случаен seed (когато играчът не е подал `--seed`)."""
    return random.SystemRandom().randrange(config.SEED_MAX)


def derive_seed(base_seed: int, *parts: object) -> int:
    """Производен seed от основния seed и етикети (напр. "map", 3).

    Използва SHA-256, а не вградения `hash()`, защото `hash()` на низове е различен при
    всяко стартиране на Python – а ние искаме пълен детерминизъм.
    """
    text = ":".join([str(base_seed), *map(str, parts)])
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % config.SEED_MAX


def make_rng(seed: int) -> random.Random:
    """Нов независим генератор, инициализиран със `seed`."""
    return random.Random(seed)

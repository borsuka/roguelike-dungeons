"""Входна точка на играта.

Употреба:
    python main.py                 # нормална игра
    python main.py --smoke 200     # headless smoke test с 200 случайни хода
"""

from __future__ import annotations

import argparse
import os


def parse_args() -> argparse.Namespace:
    """Разчита аргументите от командния ред."""
    parser = argparse.ArgumentParser(description="Roguelike с процедурно генерирани подземия")
    parser.add_argument("--smoke", type=int, metavar="N",
                        help="headless smoke test с N случайни натискания")
    return parser.parse_args()


def main() -> None:
    """Стартира играта или smoke теста."""
    args = parse_args()
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if args.smoke is not None:
        # dummy драйверът позволява pygame да работи без реален прозорец.
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        from engine.smoke import run_smoke

        report = run_smoke(args.smoke)
        print(f"Smoke test OK: {report}")
        return

    from engine.game import Game

    Game().run()


if __name__ == "__main__":
    main()

"""Тест на входната точка: `python main.py --smoke N` в отделен процес."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_main_smoke_command_runs_headless() -> None:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, "main.py", "--smoke", "200", "--seed", "3"],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert "Smoke test OK" in result.stdout

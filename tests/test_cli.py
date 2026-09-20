"""CLI argument validation tests for play.py.

These exercise `play.main()`'s argument validation directly (by patching
`sys.argv`) rather than the interactive game loop, since the loop needs a
terminal/stdin.
"""

import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLAY_PY = os.path.join(ROOT, "play.py")


def run_play(*args):
    return subprocess.run(
        [sys.executable, PLAY_PY, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_negative_max_moves_is_rejected():
    result = run_play("--self-play", "--max-moves", "-1")
    assert result.returncode != 0
    assert "--max-moves must be >= 1" in result.stderr


def test_zero_max_moves_is_rejected():
    result = run_play("--self-play", "--max-moves", "0")
    assert result.returncode != 0
    assert "--max-moves must be >= 1" in result.stderr


def test_zero_depth_is_rejected():
    result = run_play("--self-play", "--depth", "0")
    assert result.returncode != 0
    assert "--depth must be >= 1" in result.stderr


def test_self_play_with_valid_args_runs_and_exits_cleanly():
    result = run_play("--self-play", "--depth", "1", "--max-moves", "2")
    assert result.returncode == 0
    assert "AI Chess Bot" in result.stdout

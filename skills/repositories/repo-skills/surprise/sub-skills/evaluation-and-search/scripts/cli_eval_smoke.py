#!/usr/bin/env python3
"""Tiny deterministic smoke for the Surprise CLI evaluation path.

Checks help output, the missing-reader error path, and a happy-path custom-file
cross-validation run. Uses ``python -m surprise`` so it works even when the
console script directory is not on PATH.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


RATINGS = [
    ("u1", "i1", 5), ("u1", "i2", 4), ("u1", "i3", 1), ("u1", "i4", 2),
    ("u2", "i1", 4), ("u2", "i2", 5), ("u2", "i3", 2), ("u2", "i4", 1),
    ("u3", "i1", 1), ("u3", "i2", 2), ("u3", "i3", 5), ("u3", "i4", 4),
    ("u4", "i1", 2), ("u4", "i2", 1), ("u4", "i3", 4), ("u4", "i4", 5),
    ("u5", "i1", 3), ("u5", "i2", 3), ("u5", "i3", 4), ("u5", "i4", 2),
]


def write_ratings(path: Path) -> None:
    path.write_text("\n".join(f"{u} {i} {r}" for u, i, r in RATINGS) + "\n", encoding="utf-8")


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "surprise", *args],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def main() -> None:
    help_run = run_cli(["--help"])
    assert help_run.returncode == 0, help_run.stderr
    assert "-algo" in help_run.stdout and "-reader" in help_run.stdout

    with tempfile.TemporaryDirectory() as tmpdir:
        ratings_path = Path(tmpdir) / "ratings.txt"
        write_ratings(ratings_path)

        missing_reader = run_cli([
            "-algo", "NormalPredictor",
            "-load-custom", str(ratings_path),
            "-n-folds", "2",
        ])
        assert missing_reader.returncode == 2
        assert "-reader parameter is needed" in missing_reader.stderr

        reader_expr = "Reader(line_format='user item rating', sep=' ', rating_scale=(1, 5))"
        happy = run_cli([
            "-algo", "SVD",
            "-params", "{'n_epochs': 1, 'n_factors': 2, 'random_state': 0}",
            "-load-custom", str(ratings_path),
            "-reader", reader_expr,
            "-n-folds", "2",
            "-seed", "0",
        ])
        if happy.returncode != 0:
            raise AssertionError(f"CLI happy path failed\nSTDOUT:\n{happy.stdout}\nSTDERR:\n{happy.stderr}")
        assert "Evaluating RMSE, MAE" in happy.stdout
        assert "Fit time" in happy.stdout and "Test time" in happy.stdout

    print("cli evaluation smoke passed")
    print("checked --help, missing -reader error, and custom-file evaluation")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tiny deterministic Surprise cross_validate smoke.

This adapts Surprise's basic cross-validation example to a temporary local
ratings file so it never prompts for or downloads a built-in dataset.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from surprise import Dataset, Reader, SVD
from surprise.model_selection import KFold, cross_validate


RATINGS = [
    ("u1", "i1", 5), ("u1", "i2", 4), ("u1", "i3", 1), ("u1", "i4", 2),
    ("u2", "i1", 4), ("u2", "i2", 5), ("u2", "i3", 2), ("u2", "i4", 1),
    ("u3", "i1", 1), ("u3", "i2", 2), ("u3", "i3", 5), ("u3", "i4", 4),
    ("u4", "i1", 2), ("u4", "i2", 1), ("u4", "i3", 4), ("u4", "i4", 5),
    ("u5", "i1", 3), ("u5", "i2", 3), ("u5", "i3", 4), ("u5", "i4", 2),
]


def write_ratings(path: Path, rows=RATINGS) -> None:
    path.write_text("\n".join(f"{u} {i} {r}" for u, i, r in rows) + "\n", encoding="utf-8")


def load_data(path: Path):
    reader = Reader(line_format="user item rating", sep=" ", rating_scale=(1, 5))
    return Dataset.load_from_file(str(path), reader=reader)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ratings_path = Path(tmpdir) / "ratings.txt"
        write_ratings(ratings_path)
        data = load_data(ratings_path)

        algo = SVD(n_factors=2, n_epochs=2, random_state=0)
        cv = KFold(n_splits=2, random_state=0, shuffle=True)
        results = cross_validate(
            algo,
            data,
            measures=["RMSE", "MAE"],
            cv=cv,
            return_train_measures=True,
            n_jobs=1,
            verbose=False,
        )

    expected_keys = {"test_rmse", "test_mae", "train_rmse", "train_mae", "fit_time", "test_time"}
    assert expected_keys.issubset(results), sorted(results)
    assert len(results["test_rmse"]) == 2
    assert len(results["train_rmse"]) == 2

    print("cross_validate smoke passed")
    print(f"mean test RMSE: {float(results['test_rmse'].mean()):.4f}")
    print(f"mean test MAE:  {float(results['test_mae'].mean()):.4f}")


if __name__ == "__main__":
    main()

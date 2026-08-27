#!/usr/bin/env python3
"""Tiny deterministic holdout-before-search workflow for unbiased evaluation."""

from __future__ import annotations

import random
import tempfile
from pathlib import Path

from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import GridSearchCV


RATINGS = [
    ("u1", "i1", 5), ("u1", "i2", 4), ("u1", "i3", 1), ("u1", "i4", 2),
    ("u2", "i1", 4), ("u2", "i2", 5), ("u2", "i3", 2), ("u2", "i4", 1),
    ("u3", "i1", 1), ("u3", "i2", 2), ("u3", "i3", 5), ("u3", "i4", 4),
    ("u4", "i1", 2), ("u4", "i2", 1), ("u4", "i3", 4), ("u4", "i4", 5),
    ("u5", "i1", 3), ("u5", "i2", 3), ("u5", "i3", 4), ("u5", "i4", 2),
]


def write_ratings(path: Path) -> None:
    path.write_text("\n".join(f"{u} {i} {r}" for u, i, r in RATINGS) + "\n", encoding="utf-8")


def load_data(path: Path):
    reader = Reader(line_format="user item rating", sep=" ", rating_scale=(1, 5))
    return Dataset.load_from_file(str(path), reader=reader)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        ratings_path = Path(tmpdir) / "ratings.txt"
        write_ratings(ratings_path)
        data = load_data(ratings_path)

        raw_ratings = list(data.raw_ratings)
        random.Random(0).shuffle(raw_ratings)
        split_at = int(0.75 * len(raw_ratings))
        tuning_raw = raw_ratings[:split_at]
        holdout_raw = raw_ratings[split_at:]
        assert tuning_raw and holdout_raw

        # Search only on the tuning pool.
        data.raw_ratings = tuning_raw
        param_grid = {
            "n_factors": [2],
            "n_epochs": [1, 2],
            "random_state": [0],
        }
        gs = GridSearchCV(SVD, param_grid, measures=["rmse"], cv=2, refit=True, n_jobs=1)
        gs.fit(data)

        # With refit=True, the best RMSE estimator is fitted on all tuning data.
        algo = gs.best_estimator["rmse"]
        tuning_trainset = data.build_full_trainset()
        biased_predictions = algo.test(tuning_trainset.build_testset())
        holdout_testset = data.construct_testset(holdout_raw)
        holdout_predictions = algo.test(holdout_testset)

        biased_rmse = accuracy.rmse(biased_predictions, verbose=False)
        holdout_rmse = accuracy.rmse(holdout_predictions, verbose=False)
        assert len(holdout_predictions) == len(holdout_raw)

    print("unbiased split smoke passed")
    print(f"tuning ratings: {len(tuning_raw)}; holdout ratings: {len(holdout_raw)}")
    print(f"biased tuning RMSE:  {biased_rmse:.4f}")
    print(f"unbiased holdout RMSE: {holdout_rmse:.4f}")


if __name__ == "__main__":
    main()

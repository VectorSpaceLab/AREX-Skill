#!/usr/bin/env python3
"""Tiny deterministic Surprise GridSearchCV smoke.

Covers nested dict-valued sim_options and bsl_options, cv_results shapes, and
refit-enabled predict/test behavior on a temporary local dataset.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from surprise import Dataset, KNNBaseline, Reader
from surprise.model_selection import GridSearchCV, KFold


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

        param_grid = {
            "k": [2],
            "min_k": [1],
            "verbose": [False],
            "bsl_options": {
                "method": ["als"],
                "reg_u": [5, 10],
                "reg_i": [5],
            },
            "sim_options": {
                "name": ["msd", "cosine"],
                "min_support": [1],
                "user_based": [False],
            },
        }
        cv = KFold(n_splits=2, random_state=0, shuffle=True)
        gs = GridSearchCV(
            KNNBaseline,
            param_grid,
            measures=["rmse", "mae"],
            cv=cv,
            refit="rmse",
            return_train_measures=True,
            n_jobs=1,
        )
        gs.fit(data)

        n_rows = len(gs.cv_results["params"])
        assert n_rows == 4
        assert gs.cv_results["mean_test_rmse"].shape == (n_rows,)
        assert gs.cv_results["split0_train_mae"].shape == (n_rows,)
        assert gs.cv_results["rank_test_rmse"].min() == 1
        assert gs.cv_results["params"][gs.best_index["rmse"]] == gs.best_params["rmse"]

        # refit="rmse" means the RMSE-selected estimator is fitted on all data.
        prediction = gs.predict("u1", "i1")
        assert prediction.uid == "u1" and prediction.iid == "i1"
        assert len(gs.test(data.construct_testset(data.raw_ratings))) == len(RATINGS)

    print("grid search smoke passed")
    print(f"parameter rows: {n_rows}")
    print(f"best RMSE: {float(gs.best_score['rmse']):.4f}")
    print(f"best params: {gs.best_params['rmse']}")


if __name__ == "__main__":
    main()

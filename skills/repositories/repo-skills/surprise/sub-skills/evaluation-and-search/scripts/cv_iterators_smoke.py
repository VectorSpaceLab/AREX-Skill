#!/usr/bin/env python3
"""Tiny deterministic smoke for Surprise train/test and CV iterators."""

from __future__ import annotations

import tempfile
from collections import Counter
from pathlib import Path

from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import (
    KFold,
    LeaveOneOut,
    PredefinedKFold,
    RepeatedKFold,
    ShuffleSplit,
    train_test_split,
)


RATINGS = [
    ("u1", "i1", 5), ("u1", "i2", 4), ("u1", "i3", 1), ("u1", "i4", 2),
    ("u2", "i1", 4), ("u2", "i2", 5), ("u2", "i3", 2), ("u2", "i4", 1),
    ("u3", "i1", 1), ("u3", "i2", 2), ("u3", "i3", 5), ("u3", "i4", 4),
    ("u4", "i1", 2), ("u4", "i2", 1), ("u4", "i3", 4), ("u4", "i4", 5),
    ("u5", "i1", 3), ("u5", "i2", 3), ("u5", "i3", 4), ("u5", "i4", 2),
]


def write_ratings(path: Path, rows) -> None:
    path.write_text("\n".join(f"{u} {i} {r}" for u, i, r in rows) + "\n", encoding="utf-8")


def reader() -> Reader:
    return Reader(line_format="user item rating", sep=" ", rating_scale=(1, 5))


def load_file(path: Path):
    return Dataset.load_from_file(str(path), reader=reader())


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        ratings_path = tmp / "ratings.txt"
        write_ratings(ratings_path, RATINGS)
        data = load_file(ratings_path)

        trainset, testset = train_test_split(data, test_size=0.25, random_state=0)
        assert trainset.n_ratings == 15
        assert len(testset) == 5

        algo = SVD(n_factors=2, n_epochs=1, random_state=0)
        algo.fit(trainset)
        predictions = algo.test(testset)
        rmse = accuracy.rmse(predictions, verbose=False)

        kfolds = list(KFold(n_splits=4, random_state=0, shuffle=True).split(data))
        assert len(kfolds) == 4
        assert sum(len(test) for _, test in kfolds) == len(RATINGS)

        shuffle_splits = list(ShuffleSplit(n_splits=2, test_size=0.25, random_state=0).split(data))
        assert len(shuffle_splits) == 2
        assert all(train.n_ratings == 15 and len(test) == 5 for train, test in shuffle_splits)

        repeated = list(RepeatedKFold(n_splits=2, n_repeats=2, random_state=0).split(data))
        assert len(repeated) == 4

        loo_splits = list(LeaveOneOut(n_splits=2, random_state=0, min_n_ratings=1).split(data))
        assert len(loo_splits) == 2
        for _, loo_testset in loo_splits:
            per_user = Counter(uid for uid, _, _ in loo_testset)
            assert per_user and all(count == 1 for count in per_user.values())

        train_path = tmp / "fold.train"
        test_path = tmp / "fold.test"
        # Each user keeps at least one rating in train and one in test.
        train_rows = [row for row in RATINGS if row[1] in {"i1", "i2", "i3"}]
        test_rows = [row for row in RATINGS if row[1] == "i4"]
        write_ratings(train_path, train_rows)
        write_ratings(test_path, test_rows)
        folded = Dataset.load_from_folds([(str(train_path), str(test_path))], reader=reader())
        predefined = list(PredefinedKFold().split(folded))
        assert len(predefined) == 1
        assert predefined[0][0].n_ratings == len(train_rows)
        assert len(predefined[0][1]) == len(test_rows)

    print("cv iterator smoke passed")
    print(f"train_test_split RMSE: {rmse:.4f}")
    print("checked KFold, ShuffleSplit, RepeatedKFold, LeaveOneOut, and PredefinedKFold")


if __name__ == "__main__":
    main()

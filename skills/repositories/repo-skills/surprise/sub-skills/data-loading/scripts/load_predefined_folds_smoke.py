#!/usr/bin/env python
"""Smoke test for Surprise predefined fold loading.

The script creates temporary train/test files, loads them with
Dataset.load_from_folds, materializes one PredefinedKFold split, and verifies
that nonexistent fold paths fail during dataset construction.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from surprise import Dataset, Reader
from surprise.model_selection import PredefinedKFold


TRAIN_TEXT = """u1\ti1\t4\t111
u1\ti2\t0\t112
u2\ti1\t3\t113
u3\ti3\t5\t114
"""

TEST_TEXT = """u1\ti3\t2\t115
u2\ti2\t4\t116
"""


def main() -> None:
    reader = Reader(
        line_format="user item rating timestamp",
        sep="\t",
        rating_scale=(0, 5),
    )

    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        train_path = tmp / "fold1.train"
        test_path = tmp / "fold1.test"
        train_path.write_text(TRAIN_TEXT, encoding="utf-8")
        test_path.write_text(TEST_TEXT, encoding="utf-8")

        data = Dataset.load_from_folds([(str(train_path), str(test_path))], reader=reader)
        folds = list(PredefinedKFold().split(data))
        assert len(folds) == 1, len(folds)

        trainset, testset = folds[0]
        assert trainset.n_users == 3, trainset.n_users
        assert trainset.n_items == 3, trainset.n_items
        assert trainset.n_ratings == 4, trainset.n_ratings
        assert testset == [("u1", "i3", 2.0), ("u2", "i2", 4.0)], testset
        assert any(rating == 0.0 for _, _, rating in trainset.all_ratings())

        missing_path = tmp / "missing.test"
        try:
            Dataset.load_from_folds([(str(train_path), str(missing_path))], reader=reader)
        except ValueError as exc:
            assert "does not exist" in str(exc)
        else:  # pragma: no cover - should never happen in the smoke case
            raise AssertionError("missing predefined fold path was not rejected")

    print("predefined folds smoke passed: one fold loaded and missing path rejected")


if __name__ == "__main__":
    main()

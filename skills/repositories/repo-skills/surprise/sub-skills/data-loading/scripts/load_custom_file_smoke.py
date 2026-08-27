#!/usr/bin/env python
"""Smoke test for loading a custom ratings file with Surprise.

The script creates a temporary delimited ratings file, loads it with
Reader/Dataset.load_from_file, inspects the Trainset, and verifies that a bad
separator fails with the expected parser error. It performs no downloads and
uses no repository-local files.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from surprise import Dataset, Reader


RATINGS_TEXT = """user_id;item_id;rating;timestamp
u1;i1;4;1111111111
u1;i2;0;1111111112
u2;i1;2.5;1111111113
u3;i3;5;1111111114
"""


def main() -> None:
    with TemporaryDirectory() as tmpdir:
        ratings_path = Path(tmpdir) / "ratings.csv"
        ratings_path.write_text(RATINGS_TEXT, encoding="utf-8")

        reader = Reader(
            line_format="user item rating timestamp",
            sep=";",
            rating_scale=(0, 5),
            skip_lines=1,
        )
        data = Dataset.load_from_file(str(ratings_path), reader=reader)
        trainset = data.build_full_trainset()

        assert trainset.n_users == 3, trainset.n_users
        assert trainset.n_items == 3, trainset.n_items
        assert trainset.n_ratings == 4, trainset.n_ratings
        assert trainset.rating_scale == (0, 5), trainset.rating_scale

        inner_u1 = trainset.to_inner_uid("u1")
        inner_i2 = trainset.to_inner_iid("i2")
        assert trainset.knows_user(inner_u1)
        assert trainset.knows_item(inner_i2)
        assert trainset.to_raw_uid(inner_u1) == "u1"
        assert trainset.to_raw_iid(inner_i2) == "i2"
        assert any(rating == 0.0 for _, _, rating in trainset.all_ratings())

        bad_reader = Reader(
            line_format="user item rating timestamp",
            sep=",",
            rating_scale=(0, 5),
            skip_lines=1,
        )
        try:
            Dataset.load_from_file(str(ratings_path), reader=bad_reader)
        except ValueError as exc:
            assert "line_format" in str(exc) and "sep" in str(exc)
        else:  # pragma: no cover - should never happen in the smoke case
            raise AssertionError("wrong separator unexpectedly parsed the file")

    print("custom file smoke passed: 4 ratings, 3 users, 3 items, zero preserved")


if __name__ == "__main__":
    main()

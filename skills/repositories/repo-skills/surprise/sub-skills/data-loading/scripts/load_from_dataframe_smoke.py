#!/usr/bin/env python
"""Smoke test for loading Surprise data from a pandas DataFrame.

The script builds a tiny dataframe in memory, deliberately reorders columns for
the correct call, and checks the common mistake where dataframe display order is
mistaken for Surprise's required user-item-rating positional order.
"""

from __future__ import annotations

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("This smoke requires pandas. Install pandas or use file loading.") from exc

from surprise import Dataset, Reader


RATINGS = {
    "itemID": [1, 1, 2, 2, 3, 3],
    "rating": [3, 0, 4, -5, 1, 5],
    "userID": [9, 32, 2, 45, "10000", 45],
}


def main() -> None:
    df = pd.DataFrame(RATINGS)
    reader = Reader(rating_scale=(-10, 10))

    # Column names are irrelevant to Surprise; this explicit order is required.
    data = Dataset.load_from_df(df[["userID", "itemID", "rating"]], reader)
    trainset = data.build_full_trainset()

    assert trainset.n_users == 5, trainset.n_users
    assert trainset.n_items == 3, trainset.n_items
    assert trainset.n_ratings == 6, trainset.n_ratings
    assert trainset.rating_scale == (-10, 10), trainset.rating_scale

    uid_9 = trainset.to_inner_uid(9)
    uid_10000 = trainset.to_inner_uid("10000")
    iid_1 = trainset.to_inner_iid(1)
    assert trainset.knows_user(uid_9)
    assert trainset.knows_user(uid_10000)
    assert trainset.knows_item(iid_1)
    assert any(rating == 0.0 for _, _, rating in trainset.all_ratings())
    assert any(rating < 0.0 for _, _, rating in trainset.all_ratings())

    # Bad order: ratings become raw user ids, and userID values become ratings.
    bad_data = Dataset.load_from_df(df[["rating", "itemID", "userID"]], reader)
    bad_trainset = bad_data.build_full_trainset()
    try:
        bad_trainset.to_inner_uid("10000")
    except ValueError:
        pass
    else:  # pragma: no cover - should never happen in the smoke case
        raise AssertionError("bad dataframe column order preserved expected raw user id")

    print("dataframe smoke passed: explicit user-item-rating order and zero/negative ratings verified")


if __name__ == "__main__":
    main()

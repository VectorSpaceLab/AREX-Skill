"""Safe synthetic smoke test for Surprise neighbor retrieval.

The script compares user-based and item-based neighbor retrieval and checks
that an invalid similarity name fails immediately.
"""

from __future__ import annotations

import pandas as pd

from surprise import Dataset, KNNBasic, Reader


def build_trainset():
    rows = [
        ("u1", "i1", 5),
        ("u1", "i2", 4),
        ("u1", "i3", 1),
        ("u2", "i1", 4),
        ("u2", "i2", 5),
        ("u2", "i3", 2),
        ("u3", "i1", 1),
        ("u3", "i2", 2),
        ("u3", "i3", 5),
        ("u4", "i1", 2),
        ("u4", "i2", 1),
        ("u4", "i3", 4),
    ]
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(pd.DataFrame(rows, columns=["user", "item", "rating"]), reader)
    return data.build_full_trainset()


def main() -> None:
    trainset = build_trainset()

    user_algo = KNNBasic(
        k=3,
        min_k=1,
        sim_options={"name": "msd", "user_based": True},
        verbose=False,
    ).fit(trainset)
    item_algo = KNNBasic(
        k=3,
        min_k=1,
        sim_options={"name": "msd", "user_based": False},
        verbose=False,
    ).fit(trainset)

    user_inner = trainset.to_inner_uid("u1")
    item_inner = trainset.to_inner_iid("i1")

    user_neighbors = user_algo.get_neighbors(user_inner, k=3)
    item_neighbors = item_algo.get_neighbors(item_inner, k=3)

    print("user neighbors (raw)", [trainset.to_raw_uid(inner_id) for inner_id in user_neighbors])
    print("item neighbors (raw)", [trainset.to_raw_iid(inner_id) for inner_id in item_neighbors])

    assert len(user_neighbors) == 3
    assert len(item_neighbors) == 2
    assert user_neighbors != item_neighbors

    try:
        KNNBasic(sim_options={"name": "not-a-sim"}, verbose=False).fit(trainset)
    except NameError as exc:
        print("invalid similarity", exc.__class__.__name__, str(exc))
    else:
        raise AssertionError("expected invalid similarity name to fail")


if __name__ == "__main__":
    main()

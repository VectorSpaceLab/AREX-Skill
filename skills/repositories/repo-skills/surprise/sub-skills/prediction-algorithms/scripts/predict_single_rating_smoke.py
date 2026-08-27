"""Safe synthetic smoke test for Surprise prediction and batch prediction.

This script stays network-free by building a tiny in-memory dataset.
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
    algo = KNNBasic(
        k=2,
        min_k=1,
        sim_options={"name": "msd", "user_based": True},
        verbose=False,
    )
    algo.fit(trainset)

    known_pred = algo.predict("u1", "i3", r_ui=1)
    batch_preds = algo.test(trainset.build_testset()[:3])
    fallback_pred = algo.predict("ghost-user", "i1", r_ui=4)

    print("known", known_pred)
    print("known details", known_pred.details)
    print("batch size", len(batch_preds))
    print("batch first details", batch_preds[0].details)
    print("fallback", round(fallback_pred.est, 6), fallback_pred.details)

    assert not known_pred.details["was_impossible"]
    assert "actual_k" in known_pred.details
    assert len(batch_preds) == 3
    assert not batch_preds[0].details["was_impossible"]
    assert fallback_pred.details["was_impossible"]
    assert fallback_pred.est == trainset.global_mean


if __name__ == "__main__":
    main()

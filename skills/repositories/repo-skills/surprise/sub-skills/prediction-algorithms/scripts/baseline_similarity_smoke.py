"""Safe synthetic smoke test for baseline and similarity configuration.

This script demonstrates BaselineOnly, KNNBaseline, and the expected failures
for invalid baseline and similarity settings.
"""

from __future__ import annotations

import pandas as pd

from surprise import BaselineOnly, Dataset, KNNBasic, KNNBaseline, Reader


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

    als_options = {"method": "als", "n_epochs": 2, "reg_u": 12, "reg_i": 5}
    sgd_options = {"method": "sgd", "n_epochs": 2, "learning_rate": 0.01, "reg": 0.02}

    baseline_als = BaselineOnly(bsl_options=als_options, verbose=False).fit(trainset)
    baseline_sgd = BaselineOnly(bsl_options=sgd_options, verbose=False).fit(trainset)
    print("BaselineOnly ALS", round(baseline_als.predict("u1", "i1").est, 6))
    print("BaselineOnly SGD", round(baseline_sgd.predict("u1", "i1").est, 6))

    knn_baseline = KNNBaseline(
        k=2,
        min_k=1,
        sim_options={"name": "pearson_baseline", "user_based": False, "shrinkage": 10},
        bsl_options=als_options,
        verbose=False,
    ).fit(trainset)
    knn_pred = knn_baseline.predict("u1", "i1", r_ui=5)
    print("KNNBaseline", round(knn_pred.est, 6), knn_pred.details)
    assert not knn_pred.details["was_impossible"]

    try:
        BaselineOnly(bsl_options={"method": "wrong"}, verbose=False).fit(trainset)
    except ValueError as exc:
        print("invalid baseline method", exc.__class__.__name__, str(exc))
    else:
        raise AssertionError("expected invalid baseline method to fail")

    try:
        KNNBasic(sim_options={"name": "wrong"}, verbose=False).fit(trainset)
    except NameError as exc:
        print("invalid similarity name", exc.__class__.__name__, str(exc))
    else:
        raise AssertionError("expected invalid similarity name to fail")


if __name__ == "__main__":
    main()

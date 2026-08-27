"""Safe synthetic smoke test for a custom AlgoBase subclass.

The custom algorithm returns details for known ids and triggers the
PredictionImpossible fallback for unknown ids.
"""

from __future__ import annotations

import pandas as pd

from surprise import AlgoBase, Dataset, PredictionImpossible, Reader


class MeanMixAlgo(AlgoBase):
    def __init__(self):
        super().__init__()

    def fit(self, trainset):
        super().fit(trainset)
        self.user_means = {
            u: sum(r for (_, r) in ratings) / len(ratings)
            for u, ratings in trainset.ur.items()
        }
        self.item_means = {
            i: sum(r for (_, r) in ratings) / len(ratings)
            for i, ratings in trainset.ir.items()
        }
        return self

    def estimate(self, u, i):
        if not (self.trainset.knows_user(u) and self.trainset.knows_item(i)):
            raise PredictionImpossible("need known user and item")

        est = (
            self.trainset.global_mean + self.user_means[u] + self.item_means[i]
        ) / 3
        return est, {
            "source": "mean-mix",
            "user_mean": round(self.user_means[u], 3),
            "item_mean": round(self.item_means[i], 3),
        }


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
    ]
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(pd.DataFrame(rows, columns=["user", "item", "rating"]), reader)
    return data.build_full_trainset()


def main() -> None:
    trainset = build_trainset()
    algo = MeanMixAlgo().fit(trainset)

    known_pred = algo.predict("u1", "i1", r_ui=5)
    fallback_pred = algo.predict("ghost-user", "i1", r_ui=4)
    batch_preds = algo.test([("u1", "i2", 4), ("ghost-user", "i2", 2)])

    print("known", known_pred)
    print("known details", known_pred.details)
    print("fallback", fallback_pred.est, fallback_pred.details)
    print("batch", [(p.uid, p.details["was_impossible"]) for p in batch_preds])

    assert known_pred.details["source"] == "mean-mix"
    assert not known_pred.details["was_impossible"]
    assert fallback_pred.details["was_impossible"]
    assert fallback_pred.est == trainset.global_mean
    assert batch_preds[0].details["source"] == "mean-mix"
    assert batch_preds[1].details["was_impossible"]


if __name__ == "__main__":
    main()

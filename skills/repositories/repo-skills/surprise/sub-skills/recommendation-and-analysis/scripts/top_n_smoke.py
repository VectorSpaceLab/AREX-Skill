"""Tiny top-N recommendation smoke test.

This script builds a trainset from a local temporary ratings file, generates an
anti-testset, ranks the candidate items, and checks deterministic tie ordering
plus empty-candidate handling.
"""

from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

from surprise import AlgoBase, Dataset, Prediction, Reader


class ConstantAlgo(AlgoBase):
    """Return the same score for every known candidate."""

    def estimate(self, iuid, iiid):
        return 4.0


def get_top_n(predictions, n=10):
    """Return the top-N recommendation for each user."""

    top_n = defaultdict(list)
    for uid, iid, _, est, _ in predictions:
        top_n[uid].append((iid, est))

    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n


def main():
    ratings = "\n".join(
        [
            "u1,i1,5",
            "u1,i2,4",
            "u2,i1,3",
            "u2,i2,2",
            "u2,i3,1",
            "u2,i4,4",
        ]
    )

    with TemporaryDirectory() as tmpdir:
        ratings_path = Path(tmpdir) / "ratings.csv"
        ratings_path.write_text(ratings + "\n", encoding="utf-8")

        reader = Reader(line_format="user item rating", sep=",", rating_scale=(1, 5))
        data = Dataset.load_from_file(str(ratings_path), reader=reader)
        trainset = data.build_full_trainset()

        anti_testset = trainset.build_anti_testset()
        assert len(anti_testset) == trainset.n_users * trainset.n_items - trainset.n_ratings
        assert all(r == trainset.global_mean for _, _, r in anti_testset)

        algo = ConstantAlgo()
        algo.fit(trainset)

        predictions = algo.test(anti_testset)
        assert predictions
        assert all(p.details["was_impossible"] is False for p in predictions)

        top_n = get_top_n(predictions, n=2)

        assert top_n["u1"] == [("i3", 4.0), ("i4", 4.0)]
        assert "u2" not in top_n

        first = predictions[0]
        assert isinstance(first, Prediction)
        assert first.uid == "u1"
        assert first.iid in {"i3", "i4"}
        assert first.r_ui == trainset.global_mean
        assert first.est == 4.0
        assert first.details["was_impossible"] is False

        print("anti-testset size:", len(anti_testset))
        print("top_n:", dict(top_n))
        print("sample_prediction:", first)


if __name__ == "__main__":
    main()

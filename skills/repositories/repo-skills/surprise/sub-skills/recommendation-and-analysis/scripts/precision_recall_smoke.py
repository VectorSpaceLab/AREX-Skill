"""Tiny precision/recall@k smoke test with synthetic Prediction objects."""

from collections import defaultdict
from math import isclose

from surprise import Prediction


def precision_recall_at_k(predictions, k=10, threshold=3.5):
    """Return precision and recall at k metrics for each user."""

    user_est_true = defaultdict(list)
    for uid, _, true_r, est, _ in predictions:
        user_est_true[uid].append((est, true_r))

    precisions = {}
    recalls = {}
    for uid, user_ratings in user_est_true.items():
        user_ratings.sort(key=lambda x: x[0], reverse=True)

        n_rel = sum((true_r >= threshold) for (_, true_r) in user_ratings)
        n_rec_k = sum((est >= threshold) for (est, _) in user_ratings[:k])
        n_rel_and_rec_k = sum(
            ((true_r >= threshold) and (est >= threshold))
            for (est, true_r) in user_ratings[:k]
        )

        precisions[uid] = n_rel_and_rec_k / n_rec_k if n_rec_k != 0 else 0
        recalls[uid] = n_rel_and_rec_k / n_rel if n_rel != 0 else 0

    return precisions, recalls


def main():
    predictions = [
        Prediction("u_hit", "i1", 5, 4.8, {"was_impossible": False}),
        Prediction("u_hit", "i2", 2, 4.2, {"was_impossible": False}),
        Prediction("u_hit", "i3", 5, 3.2, {"was_impossible": False}),
        Prediction("u_no_rel", "i4", 2, 4.9, {"was_impossible": False}),
        Prediction("u_no_rel", "i5", 1, 4.1, {"was_impossible": False}),
        Prediction("u_no_rec", "i6", 5, 3.9, {"was_impossible": False}),
        Prediction("u_no_rec", "i7", 4, 3.2, {"was_impossible": False}),
    ]

    precisions, recalls = precision_recall_at_k(predictions, k=2, threshold=4)

    assert precisions["u_hit"] == 0.5
    assert recalls["u_hit"] == 0.5
    assert precisions["u_no_rel"] == 0
    assert recalls["u_no_rel"] == 0
    assert precisions["u_no_rec"] == 0
    assert recalls["u_no_rec"] == 0

    avg_precision = sum(precisions.values()) / len(precisions)
    avg_recall = sum(recalls.values()) / len(recalls)
    assert isclose(avg_precision, 1 / 6)
    assert isclose(avg_recall, 1 / 6)

    print("precisions:", precisions)
    print("recalls:", recalls)
    print("avg_precision:", avg_precision)
    print("avg_recall:", avg_recall)


if __name__ == "__main__":
    main()

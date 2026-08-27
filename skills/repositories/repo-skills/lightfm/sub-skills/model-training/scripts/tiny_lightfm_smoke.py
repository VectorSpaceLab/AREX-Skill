#!/usr/bin/env python3
"""No-network LightFM model-training smoke test.

The fixture is intentionally tiny and deterministic. It checks that a local
LightFM installation can train, score, export representations, and compute a
small precision summary without downloading any datasets.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Tuple


LOSSES = ("logistic", "warp", "bpr", "warp-kos")


def _pairs(values: Iterable[Tuple[int, int]], np):
    return np.asarray(list(values), dtype=np.int32)


def build_fixture(loss: str, np, sp):
    """Build a tiny train/test pair with no train-test intersections."""

    shape = (6, 8)

    positive_train = _pairs(
        [
            (0, 0),
            (0, 1),
            (1, 0),
            (1, 2),
            (2, 3),
            (2, 4),
            (3, 3),
            (3, 5),
            (4, 6),
            (4, 7),
            (5, 2),
            (5, 6),
        ],
        np,
    )
    rows = positive_train[:, 0]
    cols = positive_train[:, 1]
    data = np.ones(len(positive_train), dtype=np.float32)

    if loss == "logistic":
        # Logistic loss can use explicit negative labels. Keep them off the
        # held-out positive pairs so the precision check remains well-defined.
        negative_train = _pairs(
            [
                (0, 5),
                (0, 6),
                (1, 6),
                (2, 0),
                (3, 1),
                (4, 3),
                (5, 4),
            ],
            np,
        )
        rows = np.concatenate([rows, negative_train[:, 0]])
        cols = np.concatenate([cols, negative_train[:, 1]])
        data = np.concatenate(
            [data, -np.ones(len(negative_train), dtype=np.float32)]
        )

    rows = np.ascontiguousarray(rows, dtype=np.int32)
    cols = np.ascontiguousarray(cols, dtype=np.int32)
    data = np.ascontiguousarray(data, dtype=np.float32)
    rows = np.ascontiguousarray(rows, dtype=np.int32)
    cols = np.ascontiguousarray(cols, dtype=np.int32)
    data = np.ascontiguousarray(data, dtype=np.float32)
    train = sp.coo_matrix((data, (rows, cols)), shape=shape, dtype=np.float32)

    heldout_positive = _pairs(
        [
            (0, 2),
            (1, 1),
            (2, 5),
            (3, 4),
            (4, 0),
            (5, 7),
        ],
        np,
    )
    test_rows = np.ascontiguousarray(heldout_positive[:, 0], dtype=np.int32)
    test_cols = np.ascontiguousarray(heldout_positive[:, 1], dtype=np.int32)
    test_data = np.ones(len(heldout_positive), dtype=np.float32)
    test = sp.csr_matrix(
        (test_data, (test_rows, test_cols)),
        shape=shape,
        dtype=np.float32,
    )

    return train, test


def assert_finite(name: str, values, np) -> None:
    if not np.isfinite(values).all():
        raise RuntimeError(f"{name} contains non-finite values")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train and score a deterministic no-network LightFM fixture."
    )
    parser.add_argument(
        "--loss",
        choices=LOSSES,
        default="warp",
        help="LightFM loss to smoke-test (default: warp).",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs; 0 only initializes the model (default: 3).",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        help="Number of CPU threads for LightFM calls (default: 1).",
    )
    parser.add_argument(
        "--components",
        type=int,
        default=8,
        help="Latent components for the tiny model (default: 8).",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.05,
        help="Learning rate passed to LightFM (default: 0.05).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="k for the printed precision_at_k summary (default: 3).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for deterministic initialization/shuffling (default: 7).",
    )
    return parser.parse_args(argv)


def import_runtime():
    try:
        import numpy as np
        import scipy.sparse as sp
        from lightfm import LightFM
        from lightfm.evaluation import precision_at_k
    except Exception as exc:  # pragma: no cover - exercised by user environments.
        raise SystemExit(
            "This smoke test requires installed runtime packages: "
            "lightfm, numpy, and scipy. Original import error: "
            f"{exc}"
        ) from exc

    return np, sp, LightFM, precision_at_k


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.epochs < 0:
        raise SystemExit("--epochs must be >= 0")
    if args.threads < 1:
        raise SystemExit("--threads must be >= 1")
    if args.components < 1:
        raise SystemExit("--components must be >= 1")
    if args.k < 1:
        raise SystemExit("--k must be >= 1")

    np, sp, LightFM, precision_at_k = import_runtime()
    train, test = build_fixture(args.loss, np, sp)

    model_kwargs = {
        "loss": args.loss,
        "no_components": args.components,
        "learning_rate": args.learning_rate,
        "random_state": args.seed,
    }
    if args.loss == "warp-kos":
        # The fixture has only a few positives per user; keep k/n small.
        model_kwargs.update({"k": 2, "n": 3})

    model = LightFM(**model_kwargs)
    model.fit(train, epochs=args.epochs, num_threads=args.threads)

    n_items = train.shape[1]
    item_ids = np.arange(n_items, dtype=np.int32)
    scores = model.predict(0, item_ids, num_threads=args.threads)
    assert_finite("predictions", scores, np)

    item_biases, item_embeddings = model.get_item_representations()
    user_biases, user_embeddings = model.get_user_representations()
    assert_finite("item_biases", item_biases, np)
    assert_finite("item_embeddings", item_embeddings, np)
    assert_finite("user_biases", user_biases, np)
    assert_finite("user_embeddings", user_embeddings, np)

    precision = precision_at_k(
        model,
        test,
        train_interactions=train.tocsr(),
        k=min(args.k, n_items),
        num_threads=args.threads,
        check_intersections=True,
    )
    precision_mean = float(precision.mean()) if precision.size else float("nan")
    if not np.isfinite(precision_mean):
        raise RuntimeError("precision summary is not finite")

    filtered_scores = scores.copy()
    filtered_scores[train.tocsr()[0].indices] = -np.inf
    top_items = np.argsort(-filtered_scores)[: min(args.k, n_items)].tolist()

    print("LightFM tiny smoke OK")
    print(f"loss={args.loss} epochs={args.epochs} threads={args.threads}")
    print(f"train_shape={train.shape} train_nnz={train.nnz} test_nnz={test.nnz}")
    print(
        "score_min={:.6f} score_max={:.6f}".format(
            float(np.min(scores)), float(np.max(scores))
        )
    )
    print(f"precision_at_{min(args.k, n_items)}={precision_mean:.6f}")
    print(f"top_items_user0_excluding_train={top_items}")
    print(f"item_embedding_shape={tuple(item_embeddings.shape)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

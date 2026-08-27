#!/usr/bin/env python3
"""Safe smoke checks for AlignedUMAP and UMAP model composition.

The script uses only sklearn's bundled iris dataset: no network, downloads,
large training jobs, or writes. It validates overlapping slice relations, runs
an aligned fit, runs an online update, and optionally composes two fitted UMAP
models over the same iris rows.

Examples:
  python aligned_composition_smoke.py --json
  python aligned_composition_smoke.py --composition --json
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny AlignedUMAP, update, and optional composition smoke checks."
    )
    parser.add_argument(
        "--composition",
        action="store_true",
        help="Also compose two fitted UMAP models over the same rows.",
    )
    parser.add_argument(
        "--n-epochs",
        type=int,
        default=25,
        help="Small epoch count for quick checks.",
    )
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    return parser


def validate_relation(rel: dict[int, int], n_left: int, n_right: int) -> dict[str, object]:
    bad_keys = [int(k) for k in rel if k < 0 or k >= n_left]
    bad_values = [int(v) for v in rel.values() if v < 0 or v >= n_right]
    return {
        "pairs": len(rel),
        "valid": not bad_keys and not bad_values,
        "bad_keys": bad_keys,
        "bad_values": bad_values,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        import numpy as np
        import umap
        from sklearn.datasets import load_iris
    except ImportError as exc:
        print(
            "Install base dependencies with `pip install umap-learn scikit-learn`.",
            file=sys.stderr,
        )
        print(f"ImportError: {exc}", file=sys.stderr)
        return 2

    X, _ = load_iris(return_X_y=True)
    slices = [X[i : i + 50] for i in range(0, 75, 25)]
    # rows 25:49 of slice t correspond to rows 0:24 of slice t+1.
    relations = [{i + 25: i for i in range(25)} for _ in range(len(slices) - 1)]
    relation_checks = [
        validate_relation(rel, slices[i].shape[0], slices[i + 1].shape[0])
        for i, rel in enumerate(relations)
    ]

    summary: dict[str, object] = {
        "checks": {"relations": relation_checks},
        "warnings": [],
    }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        aligned_model = umap.AlignedUMAP(
            n_neighbors=5,
            n_epochs=args.n_epochs,
            random_state=args.random_state,
        ).fit(slices, relations=relations)

        update_model = umap.AlignedUMAP(
            n_neighbors=5,
            n_epochs=args.n_epochs,
            random_state=args.random_state,
        ).fit(slices[:2], relations=relations[:1])
        update_model.update(slices[2], relations=relations[1], n_neighbors=5)

        summary["checks"]["aligned"] = {
            "num_embeddings": len(aligned_model.embeddings_),
            "shapes": [list(e.shape) for e in aligned_model.embeddings_],
            "finite": bool(all(np.isfinite(e).all() for e in aligned_model.embeddings_)),
        }
        summary["checks"]["update"] = {
            "num_embeddings": len(update_model.embeddings_),
            "latest_shape": list(update_model.embeddings_[-1].shape),
            "finite": bool(all(np.isfinite(e).all() for e in update_model.embeddings_)),
        }

        if args.composition:
            left_view = X[:, :2]
            right_view = X[:, 2:]
            left_mapper = umap.UMAP(
                n_neighbors=10,
                n_epochs=args.n_epochs,
                random_state=args.random_state,
            ).fit(left_view)
            right_mapper = umap.UMAP(
                n_neighbors=10,
                n_epochs=args.n_epochs,
                random_state=args.random_state,
            ).fit(right_view)
            intersection = left_mapper * right_mapper
            union = left_mapper + right_mapper
            contrast = left_mapper - right_mapper
            summary["checks"]["composition"] = {
                "intersection_shape": list(intersection.embedding_.shape),
                "union_shape": list(union.embedding_.shape),
                "contrast_shape": list(contrast.embedding_.shape),
                "finite": bool(
                    np.isfinite(intersection.embedding_).all()
                    and np.isfinite(union.embedding_).all()
                    and np.isfinite(contrast.embedding_).all()
                ),
            }

    summary["warnings"] = sorted({str(w.message) for w in caught})

    failed = []
    for name, result in summary["checks"].items():
        if name == "relations":
            if not all(item["valid"] for item in result):
                failed.append(name)
        elif not result.get("finite", True):
            failed.append(name)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for name, result in summary["checks"].items():
            print(f"{name}: {result}")
        for msg in summary["warnings"]:
            print(f"warning: {msg}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

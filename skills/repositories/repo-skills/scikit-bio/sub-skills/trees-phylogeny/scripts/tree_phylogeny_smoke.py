#!/usr/bin/env python3
"""Deterministic public smoke check for scikit-bio tree APIs."""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO


def _json_error(message: str, exc: BaseException) -> int:
    payload = {
        "ok": False,
        "error": message,
        "exception_type": type(exc).__name__,
        "exception": str(exc),
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 1


def _load_skbio():
    try:
        from skbio import DistanceMatrix, TreeNode
        from skbio.tree import nj, rf_dists, upgma
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        raise RuntimeError(
            "Could not import scikit-bio tree APIs. Install scikit-bio and its "
            "runtime dependencies, then rerun this script."
        ) from exc
    return DistanceMatrix, TreeNode, nj, rf_dists, upgma


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a small Newick tree and build a tiny scikit-bio phylogeny."
    )
    parser.add_argument(
        "--algorithm",
        choices=("nj", "upgma"),
        default="nj",
        help="Distance-matrix construction algorithm to smoke test.",
    )
    parser.add_argument(
        "--newick",
        default="((A:1.0,B:2.0)C:3.0,D:4.0)root;",
        help="Small rooted Newick string with named tips and branch lengths.",
    )
    return parser.parse_args(argv)


def _validate_tree(tree) -> dict[str, object]:
    tips = [tip.name for tip in tree.tips()]
    duplicate_tips = sorted({name for name in tips if tips.count(name) > 1})
    missing_lengths = sorted(
        node.name or "<internal>"
        for node in tree.traverse(include_self=False)
        if node.length is None
    )
    if len(tree.children) != 2:
        raise ValueError("Expected a rooted tree whose root has exactly two children.")
    if duplicate_tips:
        raise ValueError(f"Expected unique tip names; found {duplicate_tips!r}.")
    if missing_lengths:
        raise ValueError(f"Expected branch lengths on all non-root nodes; missing {missing_lengths!r}.")
    if set(tips) != {"A", "B", "D"}:
        raise ValueError(f"Expected tips A, B, D; observed {tips!r}.")
    return {
        "root": tree.name,
        "tips": tips,
        "tip_count": tree.count(tips=True),
        "total_length": round(float(tree.total_length()), 6),
    }


def _build_tree(DistanceMatrix, nj, upgma, algorithm: str):
    dm = DistanceMatrix(
        [[0.0, 5.0, 9.0, 9.0],
         [5.0, 0.0, 10.0, 10.0],
         [9.0, 10.0, 0.0, 8.0],
         [9.0, 10.0, 8.0, 0.0]],
        ids=["a", "b", "c", "d"],
    )
    if algorithm == "nj":
        built = nj(dm)
    else:
        built = upgma(dm)
    built_tips = sorted(tip.name for tip in built.tips())
    if built_tips != list("abcd"):
        raise ValueError(f"Constructed tree tips do not match matrix IDs: {built_tips!r}.")
    return built, built_tips


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        DistanceMatrix, TreeNode, nj, rf_dists, upgma = _load_skbio()
        tree = TreeNode.read(StringIO(args.newick))
        parsed = _validate_tree(tree)
        built, built_tips = _build_tree(DistanceMatrix, nj, upgma, args.algorithm)
        comparison = rf_dists([built, built.copy()], ids=["built", "copy"])
        payload = {
            "ok": True,
            "algorithm": args.algorithm,
            "parsed": parsed,
            "constructed_tip_count": len(built_tips),
            "constructed_tips": built_tips,
            "self_rf_distance": float(comparison.data[0, 1]),
        }
    except Exception as exc:
        return _json_error("tree phylogeny smoke check failed", exc)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

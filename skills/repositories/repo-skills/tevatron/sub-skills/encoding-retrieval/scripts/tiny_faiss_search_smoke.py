#!/usr/bin/env python3
"""Tiny FAISS smoke test for Tevatron's flat search API.

This script does not load a model or dataset. It creates synthetic query and
passage embeddings, searches with tevatron.retriever.searcher.FaissFlatSearcher,
and verifies deterministic qid/pid/score output.

FAISS is optional in minimal Tevatron environments. By default, missing FAISS or
Tevatron search imports produce a clear SKIP message and exit successfully. Use
--strict when a dependency-missing skip should fail CI.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny Tevatron FAISS search smoke test.")
    parser.add_argument("--output", help="Optional path to write qid/pid/score text rankings.")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size for batch_search; use <=0 for search().")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero instead of skipping when optional dependencies are missing.")
    return parser.parse_args()


def skip_or_fail(message: str, strict: bool) -> None:
    prefix = "FAIL" if strict else "SKIP"
    print(f"{prefix}: {message}")
    if strict:
        raise SystemExit(2)


def main() -> None:
    args = parse_args()

    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - message is for CLI users
        skip_or_fail(f"Could not import numpy. Install numpy before running this smoke test. Details: {exc}", args.strict)
        return

    try:
        import faiss  # noqa: F401
    except Exception as exc:  # pragma: no cover - message is for CLI users
        skip_or_fail(
            "Could not import faiss. Install faiss-cpu for CPU validation or a CUDA-compatible GPU FAISS build for GPU search. "
            f"Details: {exc}",
            args.strict,
        )
        return

    try:
        from tevatron.retriever.searcher import FaissFlatSearcher
    except Exception as exc:  # pragma: no cover - message is for CLI users
        skip_or_fail(f"Could not import tevatron.retriever.searcher.FaissFlatSearcher. Details: {exc}", args.strict)
        return

    passage_ids = ["p0", "p1", "p2"]
    query_ids = ["q0", "q1"]
    passage_reps = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.5, 0.5, 0.0],
        ],
        dtype="float32",
    )
    query_reps = np.asarray(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype="float32",
    )

    searcher = FaissFlatSearcher(passage_reps)
    searcher.add(passage_reps)

    if args.batch_size > 0:
        scores, indices = searcher.batch_search(query_reps, k=2, batch_size=args.batch_size, quiet=True)
    else:
        scores, indices = searcher.search(query_reps, k=2)

    top_ids = [[passage_ids[index] for index in row] for row in indices]
    expected_top_ids = [["p0", "p2"], ["p1", "p2"]]
    if top_ids != expected_top_ids:
        raise SystemExit(f"unexpected top ids: {top_ids!r} != {expected_top_ids!r}")

    expected_scores = np.asarray([[1.0, 0.5], [1.0, 0.5]], dtype="float32")
    if not np.allclose(scores, expected_scores):
        raise SystemExit(f"unexpected scores: {scores!r} != {expected_scores!r}")

    lines = []
    for qid, score_row, index_row in zip(query_ids, scores, indices):
        for score, index in zip(score_row, index_row):
            lines.append(f"{qid}\t{passage_ids[index]}\t{float(score)}")

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {len(lines)} ranking rows to {output}.")
    else:
        print("\n".join(lines))

    print("FAISS smoke test passed.")


if __name__ == "__main__":
    main()

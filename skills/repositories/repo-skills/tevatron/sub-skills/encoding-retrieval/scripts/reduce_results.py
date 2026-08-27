#!/usr/bin/env python3
"""Merge Tevatron text ranking shards deterministically.

Input files must contain whitespace-separated rows:

    query_id passage_id score

The output uses Tevatron's tab-separated text ranking format:

    query_id<TAB>passage_id<TAB>score
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Iterable


def iter_result_files(results_dir: Path) -> Iterable[Path]:
    if not results_dir.exists():
        raise SystemExit(f"results_dir does not exist: {results_dir}")
    if not results_dir.is_dir():
        raise SystemExit(f"results_dir is not a directory: {results_dir}")
    files = sorted(path for path in results_dir.iterdir() if path.is_file())
    if not files:
        raise SystemExit(f"no result files found in: {results_dir}")
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reduce Tevatron retrieval results from multiple shards.")
    parser.add_argument("--results_dir", required=True, help="Directory containing per-shard text ranking files.")
    parser.add_argument("--output", required=True, help="Path to the merged text ranking file.")
    parser.add_argument("--depth", type=int, default=100, help="Maximum documents to keep per query after merging.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.depth <= 0:
        raise SystemExit("--depth must be a positive integer")

    results_dir = Path(args.results_dir)
    output = Path(args.output)
    all_results: DefaultDict[str, list[tuple[str, float]]] = defaultdict(list)

    files = list(iter_result_files(results_dir))
    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) != 3:
                    raise SystemExit(f"{path}:{line_number}: expected 3 columns, found {len(parts)}")
                qid, docid, score_text = parts
                try:
                    score = float(score_text)
                except ValueError as exc:
                    raise SystemExit(f"{path}:{line_number}: invalid score {score_text!r}") from exc
                all_results[qid].append((docid, score))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for qid in sorted(all_results):
            ranked = sorted(all_results[qid], key=lambda item: (-item[1], item[0]))[: args.depth]
            for docid, score in ranked:
                handle.write(f"{qid}\t{docid}\t{score}\n")

    print(f"Merged {len(files)} files for {len(all_results)} queries into {output} at depth {args.depth}.")


if __name__ == "__main__":
    main()

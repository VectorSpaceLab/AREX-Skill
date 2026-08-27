#!/usr/bin/env python3
"""Validate ColBERT TSV/JSONL data contracts without importing ColBERT."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable


class ValidationError(ValueError):
    """Raised when a data file violates a ColBERT data contract."""


def fail(message: str) -> None:
    raise ValidationError(message)


def parse_int(value: str, context: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        fail(f"{context}: expected integer, got {value!r}")
        raise exc


def read_lines(path: Path) -> Iterable[tuple[int, str]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            yield line_number, line.rstrip("\n")


def validate_two_column_tsv(path: Path, label: str, require_int_ids: bool) -> set[int | str]:
    ids: set[int | str] = set()
    rows = 0
    for line_number, line in read_lines(path):
        if not line:
            fail(f"{path}:{line_number}: empty {label} row")
        parts = line.split("\t")
        if len(parts) != 2:
            fail(f"{path}:{line_number}: expected 2 tab-separated columns for {label}, got {len(parts)}")
        row_id, text = parts
        if row_id == "":
            fail(f"{path}:{line_number}: empty {label} id")
        if text == "":
            fail(f"{path}:{line_number}: empty {label} text")
        normalized_id: int | str = parse_int(row_id, f"{path}:{line_number} {label} id") if require_int_ids else row_id
        if normalized_id in ids:
            fail(f"{path}:{line_number}: duplicate {label} id {row_id!r}")
        ids.add(normalized_id)
        rows += 1
    if rows == 0:
        fail(f"{path}: no {label} rows found")
    return ids


def validate_qrels(path: Path) -> dict[int, set[int]]:
    positives: dict[int, set[int]] = defaultdict(set)
    rows = 0
    for line_number, line in read_lines(path):
        if not line:
            fail(f"{path}:{line_number}: empty qrels row")
        parts = line.split()
        if len(parts) != 4:
            fail(f"{path}:{line_number}: expected 4 whitespace-separated qrels columns, got {len(parts)}")
        qid = parse_int(parts[0], f"{path}:{line_number} qid")
        pid = parse_int(parts[2], f"{path}:{line_number} pid")
        label = parse_int(parts[3], f"{path}:{line_number} label")
        if label != 1:
            fail(f"{path}:{line_number}: ColBERT MSMARCO utility expects label 1, got {label}")
        positives[qid].add(pid)
        rows += 1
    if rows == 0:
        fail(f"{path}: no qrels rows found")
    return positives


def validate_ranking(path: Path, require_score: bool = False) -> dict[int, list[tuple[int, int, float | None]]]:
    rankings: dict[int, list[tuple[int, int, float | None]]] = defaultdict(list)
    seen_ranks: set[tuple[int, int]] = set()
    rows = 0
    for line_number, line in read_lines(path):
        if not line:
            fail(f"{path}:{line_number}: empty ranking row")
        parts = line.split("\t")
        if len(parts) not in (3, 4):
            fail(f"{path}:{line_number}: expected 3 or 4 ranking columns, got {len(parts)}")
        if require_score and len(parts) != 4:
            fail(f"{path}:{line_number}: score column is required")
        qid = parse_int(parts[0], f"{path}:{line_number} qid")
        pid = parse_int(parts[1], f"{path}:{line_number} pid")
        rank = parse_int(parts[2], f"{path}:{line_number} rank")
        if rank < 1:
            fail(f"{path}:{line_number}: rank must start at 1, got {rank}")
        score = None
        if len(parts) == 4:
            try:
                score = float(parts[3])
            except ValueError as exc:
                fail(f"{path}:{line_number}: expected numeric score, got {parts[3]!r}")
                raise exc
        rank_key = (qid, rank)
        if rank_key in seen_ranks:
            fail(f"{path}:{line_number}: duplicate rank {rank} for qid {qid}")
        seen_ranks.add(rank_key)
        rankings[qid].append((rank, pid, score))
        rows += 1
    if rows == 0:
        fail(f"{path}: no ranking rows found")

    for qid, rows_for_qid in rankings.items():
        ranks = sorted(rank for rank, _, _ in rows_for_qid)
        expected = list(range(1, len(ranks) + 1))
        if ranks != expected:
            fail(f"{path}: qid {qid} ranks must be sequential from 1; found {ranks[:10]}")
    return rankings


def validate_lotte_qas(path: Path) -> dict[int, set[int]]:
    qas: dict[int, set[int]] = {}
    rows = 0
    for line_number, line in read_lines(path):
        if not line:
            fail(f"{path}:{line_number}: empty JSONL row")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"{path}:{line_number}: invalid JSON: {exc}")
        if "qid" not in payload:
            fail(f"{path}:{line_number}: missing qid")
        if "answer_pids" not in payload:
            fail(f"{path}:{line_number}: missing answer_pids")
        qid = int(payload["qid"])
        if qid in qas:
            fail(f"{path}:{line_number}: duplicate qid {qid}")
        answer_pids = payload["answer_pids"]
        if not isinstance(answer_pids, list) or not answer_pids:
            fail(f"{path}:{line_number}: answer_pids must be a non-empty list")
        try:
            qas[qid] = {int(pid) for pid in answer_pids}
        except (TypeError, ValueError) as exc:
            fail(f"{path}:{line_number}: answer_pids must contain integer-compatible IDs")
            raise exc
        rows += 1
    if rows == 0:
        fail(f"{path}: no QA rows found")
    return qas


def require_sequential_ids(ids: set[int], label: str) -> None:
    if not ids:
        return
    expected = set(range(0, max(ids) + 1))
    if ids != expected:
        missing = sorted(expected - ids)[:10]
        fail(f"{label} must be sequential from 0; missing {missing}, found min={min(ids)} max={max(ids)} count={len(ids)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ColBERT collection/query/ranking/qrels/LoTTE QA files.",
        epilog=(
            "Examples: python validate_colbert_data.py --collection collection.tsv --queries queries.tsv "
            "--ranking ranking.tsv --qrels qrels.tsv; python validate_colbert_data.py --ranking lotte.tsv "
            "--lotte-qas qas.search.jsonl --require-score --require-sequential-qids"
        ),
    )
    parser.add_argument("--collection", type=Path, help="Two-column pid<TAB>passage TSV")
    parser.add_argument("--queries", type=Path, help="Two-column qid<TAB>query TSV")
    parser.add_argument("--ranking", type=Path, help="Three/four-column ranking TSV")
    parser.add_argument("--qrels", type=Path, help="MSMARCO-style qid 0 pid 1 qrels file")
    parser.add_argument("--lotte-qas", type=Path, help="LoTTE qas.search/forum.jsonl file")
    parser.add_argument("--require-score", action="store_true", help="Require ranking score column")
    parser.add_argument("--require-sequential-qids", action="store_true", help="Require ranking/QA/query qids to be sequential from 0")
    parser.add_argument(
        "--allow-ranking-qids-without-judgments",
        action="store_true",
        help="Warn instead of failing when ranking qids are absent from qrels/QA data",
    )
    args = parser.parse_args()

    try:
        collection_ids = validate_two_column_tsv(args.collection, "collection", True) if args.collection else None
        query_ids = validate_two_column_tsv(args.queries, "query", True) if args.queries else None
        qrels = validate_qrels(args.qrels) if args.qrels else None
        qas = validate_lotte_qas(args.lotte_qas) if args.lotte_qas else None
        rankings = validate_ranking(args.ranking, args.require_score) if args.ranking else None

        if rankings and collection_ids is not None:
            missing_pids = sorted({pid for rows in rankings.values() for _, pid, _ in rows} - set(collection_ids))
            if missing_pids:
                fail(f"ranking contains pids not present in collection: {missing_pids[:10]}")

        judgment_qids = None
        if qrels is not None:
            judgment_qids = set(qrels)
        if qas is not None:
            judgment_qids = set(qas) if judgment_qids is None else judgment_qids & set(qas)
        if rankings and judgment_qids is not None:
            missing_qids = sorted(set(rankings) - judgment_qids)
            if missing_qids:
                message = f"ranking contains qids without judgments: {missing_qids[:10]}"
                if args.allow_ranking_qids_without_judgments:
                    print(f"WARNING: {message}", file=sys.stderr)
                else:
                    fail(message)

        if rankings and query_ids is not None:
            missing_query_rows = sorted(set(rankings) - set(query_ids))
            if missing_query_rows:
                fail(f"ranking contains qids not present in queries: {missing_query_rows[:10]}")

        if args.require_sequential_qids:
            if query_ids is not None:
                require_sequential_ids(set(query_ids), "query ids")
            if qas is not None:
                require_sequential_ids(set(qas), "LoTTE QA qids")
            if rankings is not None:
                require_sequential_ids(set(rankings), "ranking qids")

        summary = {
            "collection_rows": len(collection_ids) if collection_ids is not None else None,
            "query_rows": len(query_ids) if query_ids is not None else None,
            "qrels_qids": len(qrels) if qrels is not None else None,
            "lotte_qas": len(qas) if qas is not None else None,
            "ranking_qids": len(rankings) if rankings is not None else None,
            "ranking_rows": sum(len(rows) for rows in rankings.values()) if rankings is not None else None,
        }
        print(json.dumps({k: v for k, v in summary.items() if v is not None}, indent=2, sort_keys=True))
        return 0
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

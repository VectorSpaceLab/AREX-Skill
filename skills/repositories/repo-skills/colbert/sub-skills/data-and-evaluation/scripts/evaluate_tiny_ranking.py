#!/usr/bin/env python3
"""Evaluate MSMARCO-style or tiny LoTTE-style ColBERT rankings."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


class EvaluationError(ValueError):
    """Raised when inputs cannot be evaluated safely."""


def parse_qrels(path: Path) -> dict[int, set[int]]:
    positives: dict[int, set[int]] = defaultdict(set)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            parts = line.strip().split()
            if not parts:
                continue
            if len(parts) != 4:
                raise EvaluationError(f"{path}:{line_number}: expected qid 0 pid label")
            try:
                qid, _, pid, label = map(int, parts)
            except ValueError as exc:
                raise EvaluationError(f"{path}:{line_number}: qrels qid/pid/label must be integers") from exc
            if label != 1:
                raise EvaluationError(f"{path}:{line_number}: expected positive label 1, got {label}")
            positives[qid].add(pid)
    if not positives:
        raise EvaluationError(f"{path}: no qrels found")
    return positives


def parse_lotte_qas(path: Path) -> dict[int, set[int]]:
    qas: dict[int, set[int]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise EvaluationError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if "qid" not in payload or "answer_pids" not in payload:
                raise EvaluationError(f"{path}:{line_number}: expected qid and answer_pids")
            qid = int(payload["qid"])
            if qid in qas:
                raise EvaluationError(f"{path}:{line_number}: duplicate qid {qid}")
            answer_pids = payload["answer_pids"]
            if not isinstance(answer_pids, list) or not answer_pids:
                raise EvaluationError(f"{path}:{line_number}: answer_pids must be a non-empty list")
            qas[qid] = {int(pid) for pid in answer_pids}
    if not qas:
        raise EvaluationError(f"{path}: no LoTTE QA rows found")
    return qas


def parse_ranking(path: Path, require_score: bool = False) -> dict[int, list[tuple[int, int, float | None]]]:
    rankings: dict[int, list[tuple[int, int, float | None]]] = defaultdict(list)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            parts = line.rstrip("\n").split("\t")
            if parts == [""]:
                continue
            if len(parts) not in (3, 4):
                raise EvaluationError(f"{path}:{line_number}: expected qid<TAB>pid<TAB>rank[<TAB>score]")
            if require_score and len(parts) != 4:
                raise EvaluationError(f"{path}:{line_number}: score column is required")
            try:
                qid, pid, rank = map(int, parts[:3])
                score = float(parts[3]) if len(parts) == 4 else None
            except ValueError as exc:
                raise EvaluationError(f"{path}:{line_number}: ranking qid/pid/rank/score has invalid numeric value") from exc
            if rank < 1:
                raise EvaluationError(f"{path}:{line_number}: rank must be 1-indexed")
            rankings[qid].append((rank, pid, score))
    if not rankings:
        raise EvaluationError(f"{path}: no ranking rows found")
    for qid, rows in rankings.items():
        rows.sort(key=lambda item: item[0])
        ranks = [rank for rank, _, _ in rows]
        expected = list(range(1, len(rows) + 1))
        if ranks != expected:
            raise EvaluationError(f"{path}: qid {qid} ranks must be sequential from 1")
        pids = [pid for _, pid, _ in rows]
        if len(set(pids)) != len(pids):
            raise EvaluationError(f"{path}: qid {qid} contains duplicate pids")
    return rankings


def compute_msmarco_metrics(
    qrels: dict[int, set[int]], rankings: dict[int, list[tuple[int, int, float | None]]], depths: list[int]
) -> dict[str, object]:
    ranked_without_qrels = sorted(set(rankings) - set(qrels))
    if ranked_without_qrels:
        raise EvaluationError(f"ranking qids missing from qrels: {ranked_without_qrels[:10]}")

    reciprocal_sum = 0.0
    recall_sums = {depth: 0.0 for depth in depths}
    per_query = {}

    for qid in sorted(qrels):
        positives = qrels[qid]
        rows = rankings.get(qid, [])
        reciprocal = 0.0
        recall_hits = {depth: 0.0 for depth in depths}

        for rank, pid, _ in rows:
            if pid in positives:
                if rank <= 10 and reciprocal == 0.0:
                    reciprocal = 1.0 / rank
                for depth in depths:
                    if rank <= depth:
                        recall_hits[depth] += 1.0 / len(positives)

        reciprocal_sum += reciprocal
        for depth in depths:
            recall_sums[depth] += recall_hits[depth]
        per_query[str(qid)] = {
            "mrr@10": reciprocal,
            **{f"recall@{depth}": recall_hits[depth] for depth in depths},
        }

    denominator = len(qrels)
    return {
        "mode": "msmarco",
        "num_judged_queries": len(qrels),
        "num_ranked_queries": len(rankings),
        "mrr@10": reciprocal_sum / denominator,
        "recall": {str(depth): recall_sums[depth] / denominator for depth in depths},
        "per_query": per_query,
    }


def compute_lotte_success(
    qas: dict[int, set[int]], rankings: dict[int, list[tuple[int, int, float | None]]], success_at: int
) -> dict[str, object]:
    ranked_without_qas = sorted(set(rankings) - set(qas))
    if ranked_without_qas:
        raise EvaluationError(f"ranking qids missing from LoTTE QA data: {ranked_without_qas[:10]}")

    successes = 0
    missing_rankings = []
    per_query = {}
    for qid in sorted(qas):
        answer_pids = qas[qid]
        rows = rankings.get(qid, [])
        if not rows:
            missing_rankings.append(qid)
        top_pids = [pid for rank, pid, _ in rows if rank <= success_at]
        hit = bool(set(top_pids).intersection(answer_pids))
        successes += int(hit)
        per_query[str(qid)] = {
            f"success@{success_at}": hit,
            "top_pids": top_pids,
            "answer_pids": sorted(answer_pids),
        }

    return {
        "mode": "lotte",
        "num_qas": len(qas),
        "num_ranked_queries": len(rankings),
        "missing_ranking_qids": missing_rankings,
        f"success@{success_at}": 100.0 * successes / len(qas),
        "per_query": per_query,
    }


def write_annotations(path: Path, rankings: dict[int, list[tuple[int, int, float | None]]], positives: dict[int, set[int]], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise EvaluationError(f"annotation output exists: {path}")
    with path.open("w", encoding="utf-8") as handle:
        for qid in sorted(rankings):
            positive_pids = positives.get(qid, set())
            for rank, pid, score in rankings[qid]:
                label = int(pid in positive_pids)
                fields: list[int | float] = [qid, pid, rank]
                if score is not None:
                    fields.append(score)
                fields.append(label)
                handle.write("\t".join(map(str, fields)) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute ColBERT/MSMARCO-style MRR@10/Recall@k or tiny LoTTE Success@k for a ranking TSV.",
        epilog=(
            "MSMARCO fixture: qrels '0 0 0 1; 1 0 2 1' and ranking qid0 pid1 rank1, "
            "qid0 pid0 rank2, qid1 pid2 rank1 gives MRR@10=0.75. LoTTE fixture with answer_pids "
            "[0] and [2] gives Success@1=50.0 and Success@2=100.0."
        ),
    )
    parser.add_argument("--qrels", type=Path, help="MSMARCO-style qrels file")
    parser.add_argument("--lotte-qas", type=Path, help="LoTTE qas.search/forum.jsonl file")
    parser.add_argument("--ranking", required=True, type=Path, help="Ranking TSV with qid, pid, rank, optional score")
    parser.add_argument("--depths", nargs="+", type=int, default=[50, 200, 1000, 5000, 10000], help="MSMARCO recall depths")
    parser.add_argument("--success-at", type=int, default=5, help="LoTTE Success@k depth")
    parser.add_argument("--annotate", type=Path, help="Optional output path for labeled ranking rows")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting --annotate output")
    parser.add_argument("--no-per-query", action="store_true", help="Omit per-query metrics from JSON output")
    args = parser.parse_args()

    try:
        if bool(args.qrels) == bool(args.lotte_qas):
            raise EvaluationError("provide exactly one of --qrels or --lotte-qas")
        depths = sorted(set(args.depths))
        if any(depth < 1 for depth in depths):
            raise EvaluationError("all depths must be positive")
        if args.success_at < 1:
            raise EvaluationError("--success-at must be positive")

        rankings = parse_ranking(args.ranking, require_score=bool(args.lotte_qas))
        if args.qrels:
            qrels = parse_qrels(args.qrels)
            metrics = compute_msmarco_metrics(qrels, rankings, depths)
            positives = qrels
        else:
            qas = parse_lotte_qas(args.lotte_qas)
            metrics = compute_lotte_success(qas, rankings, args.success_at)
            positives = qas

        if args.no_per_query:
            metrics.pop("per_query", None)
        if args.annotate:
            write_annotations(args.annotate, rankings, positives, args.overwrite)
            metrics["annotation"] = str(args.annotate)
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0
    except EvaluationError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate TREC run files and optional qrels before Pyserini evaluation or fusion."""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path


class ValidationIssue:
    def __init__(self, severity: str, message: str) -> None:
        self.severity = severity
        self.message = message


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def read_nonempty_lines(path: Path) -> list[tuple[int, str]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return [(number, line.strip()) for number, line in enumerate(handle, start=1) if line.strip()]
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc}") from exc


def parse_run(path: Path, require_q0: bool, strict_ranks: bool) -> tuple[list[dict[str, object]], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    rows: list[dict[str, object]] = []
    seen_pairs: set[tuple[str, str]] = set()
    ranks_by_qid: dict[str, list[int]] = defaultdict(list)
    scores_by_qid: dict[str, list[float]] = defaultdict(list)

    for line_number, line in read_nonempty_lines(path):
        parts = line.split()
        if len(parts) == 3:
            issues.append(ValidationIssue("error", f"line {line_number}: looks like MS MARCO format; convert to TREC first"))
            continue
        if len(parts) != 6:
            issues.append(ValidationIssue("error", f"line {line_number}: expected 6 columns, found {len(parts)}"))
            continue

        qid, q0, docid, rank_text, score_text, tag = parts
        if require_q0 and q0 != "Q0":
            issues.append(ValidationIssue("error", f"line {line_number}: column 2 should be Q0, found {q0!r}"))
        elif q0 != "Q0":
            issues.append(ValidationIssue("warning", f"line {line_number}: column 2 is {q0!r}, expected conventional Q0"))

        try:
            rank = int(rank_text)
            if rank <= 0:
                raise ValueError
        except ValueError:
            issues.append(ValidationIssue("error", f"line {line_number}: rank must be a positive integer, found {rank_text!r}"))
            continue

        try:
            score = float(score_text)
            if not math.isfinite(score):
                raise ValueError
        except ValueError:
            issues.append(ValidationIssue("error", f"line {line_number}: score must be finite, found {score_text!r}"))
            continue

        pair = (qid, docid)
        if pair in seen_pairs:
            issues.append(ValidationIssue("warning", f"line {line_number}: duplicate qid/docid pair {qid!r}/{docid!r}"))
        seen_pairs.add(pair)

        ranks_by_qid[qid].append(rank)
        scores_by_qid[qid].append(score)
        rows.append({"qid": qid, "docid": docid, "rank": rank, "score": score, "tag": tag, "line": line_number})

    for qid, ranks in ranks_by_qid.items():
        if len(ranks) != len(set(ranks)):
            issues.append(ValidationIssue("warning", f"qid {qid!r}: duplicate rank values found"))
        if strict_ranks:
            expected = list(range(1, len(ranks) + 1))
            if sorted(ranks) != expected:
                issues.append(ValidationIssue("error", f"qid {qid!r}: ranks should be exactly 1..{len(ranks)}"))
        scores = scores_by_qid[qid]
        if any(scores[index] < scores[index + 1] for index in range(len(scores) - 1)):
            issues.append(ValidationIssue("warning", f"qid {qid!r}: scores are not monotonically descending in file order"))

    return rows, issues


def parse_qrels(path: Path) -> tuple[dict[str, set[str]], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    qrels: dict[str, set[str]] = defaultdict(set)

    for line_number, line in read_nonempty_lines(path):
        parts = line.split()
        if len(parts) != 4:
            issues.append(ValidationIssue("error", f"qrels line {line_number}: expected 4 columns, found {len(parts)}"))
            continue
        qid, _, docid, grade_text = parts
        try:
            int(grade_text)
        except ValueError:
            issues.append(ValidationIssue("warning", f"qrels line {line_number}: relevance grade is not an integer: {grade_text!r}"))
        qrels[qid].add(docid)

    return qrels, issues


def compare_with_qrels(rows: list[dict[str, object]], qrels: dict[str, set[str]], max_examples: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    run_topics = {str(row["qid"]) for row in rows}
    qrels_topics = set(qrels)

    missing_qrels_topics = sorted(run_topics - qrels_topics)
    unused_qrels_topics = sorted(qrels_topics - run_topics)
    if missing_qrels_topics:
        examples = ", ".join(missing_qrels_topics[:max_examples])
        issues.append(ValidationIssue("warning", f"run has {len(missing_qrels_topics)} topic(s) absent from qrels: {examples}"))
    if unused_qrels_topics:
        examples = ", ".join(unused_qrels_topics[:max_examples])
        issues.append(ValidationIssue("warning", f"qrels have {len(unused_qrels_topics)} topic(s) absent from run: {examples}"))

    unjudged: list[tuple[str, str]] = []
    judged_hits = 0
    for row in rows:
        qid = str(row["qid"])
        docid = str(row["docid"])
        if qid in qrels and docid in qrels[qid]:
            judged_hits += 1
        else:
            unjudged.append((qid, docid))

    if rows:
        judged_fraction = judged_hits / len(rows)
        if unjudged:
            examples = ", ".join(f"{qid}/{docid}" for qid, docid in unjudged[:max_examples])
            issues.append(ValidationIssue("warning", f"{len(unjudged)} of {len(rows)} run rows are unjudged ({judged_fraction:.1%} judged); examples: {examples}"))

    return issues


def print_summary(rows: list[dict[str, object]], qrels: dict[str, set[str]] | None) -> None:
    topics = sorted({str(row["qid"]) for row in rows})
    tags = sorted({str(row["tag"]) for row in rows})
    max_depth = max((int(row["rank"]) for row in rows), default=0)
    print(f"rows: {len(rows)}")
    print(f"topics: {len(topics)}")
    print(f"max_rank: {max_depth}")
    print(f"tags: {', '.join(tags[:10]) if tags else '(none)'}")
    if qrels is not None:
        qrels_pairs = sum(len(docids) for docids in qrels.values())
        print(f"qrels_topics: {len(qrels)}")
        print(f"qrels_pairs: {qrels_pairs}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a TREC run and optionally compare it with qrels.")
    parser.add_argument("run", type=Path, help="Six-column TREC run file to validate.")
    parser.add_argument("--qrels", type=Path, help="Optional four-column TREC qrels file.")
    parser.add_argument("--require-q0", action="store_true", help="Treat a non-Q0 second column as an error instead of a warning.")
    parser.add_argument("--strict-ranks", action="store_true", help="Require each query's ranks to be exactly 1..depth.")
    parser.add_argument("--summary", action="store_true", help="Print row/topic/tag and optional qrels coverage summary.")
    parser.add_argument("--max-unjudged-examples", type=positive_int, default=10, help="Maximum qrels mismatch examples to print.")
    args = parser.parse_args(argv)

    rows, issues = parse_run(args.run, require_q0=args.require_q0, strict_ranks=args.strict_ranks)
    qrels = None
    if args.qrels:
        qrels, qrels_issues = parse_qrels(args.qrels)
        issues.extend(qrels_issues)
        if rows and qrels:
            issues.extend(compare_with_qrels(rows, qrels, args.max_unjudged_examples))

    if args.summary:
        print_summary(rows, qrels)

    for issue in issues:
        print(f"{issue.severity}: {issue.message}", file=sys.stderr)

    has_errors = any(issue.severity == "error" for issue in issues)
    if has_errors:
        return 1
    print("validation passed" if not issues else "validation passed with warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

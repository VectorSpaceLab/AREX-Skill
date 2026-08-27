#!/usr/bin/env python3
"""Convert Tevatron-style ranking rows to TREC run format.

Accepted input rows:
  qid docid score
  qid docid rank score
  qid Q0 docid rank score tag

Output rows are:
  qid Q0 docid rank score dense

Ranks are recomputed per contiguous query block, matching Tevatron's original
converter behavior. Sort/group input by qid in desired ranking order first.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_row(line: str, line_number: int) -> tuple[str, str, str]:
    parts = line.strip().split()
    if not parts:
        raise ValueError("blank line")
    if len(parts) == 3:
        qid, docid, score = parts
        return qid, docid, score
    if len(parts) == 4:
        qid, docid, _rank, score = parts
        if docid in {"0", "Q0"}:
            raise ValueError(
                f"line {line_number}: four-column row looks like qrels; "
                "expected ranking as qid docid rank score"
            )
        return qid, docid, score
    if len(parts) >= 6:
        qid, _q0, docid, _rank, score, *_rest = parts
        return qid, docid, score
    raise ValueError(
        f"line {line_number}: expected 3 columns (qid docid score), "
        f"4 columns (qid docid rank score), or at least 6 TREC columns; got {len(parts)}"
    )


def convert(input_path: Path, output_path: Path, remove_query: bool = False, tag: str = "dense") -> int:
    rows_written = 0
    current_qid: str | None = None
    rank = 0
    with input_path.open("r", encoding="utf-8") as source, output_path.open("w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            qid, docid, score = parse_row(line, line_number)
            try:
                float(score)
            except ValueError as exc:
                raise ValueError(f"line {line_number}: score is not numeric: {score!r}") from exc
            if current_qid != qid:
                current_qid = qid
                rank = 0
            if remove_query and qid == docid:
                continue
            rank += 1
            rows_written += 1
            target.write(f"{qid} Q0 {docid} {rank} {score} {tag}\n")
    return rows_written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input ranking file")
    parser.add_argument("--output", required=True, type=Path, help="Output TREC run file")
    parser.add_argument("--remove_query", action="store_true", help="Skip rows where qid equals docid")
    parser.add_argument("--tag", default="dense", help="Run tag to write in the last TREC column")
    args = parser.parse_args(argv)

    try:
        rows_written = convert(args.input, args.output, args.remove_query, args.tag)
    except OSError as exc:
        print(f"I/O error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"conversion error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {rows_written} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

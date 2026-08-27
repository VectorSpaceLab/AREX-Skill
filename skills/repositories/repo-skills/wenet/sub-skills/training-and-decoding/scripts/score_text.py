#!/usr/bin/env python3
"""Tiny WER/CER scorer for WeNet skill usability checks.

Input files use '<key> <text>' lines. The helper aligns matching utterance keys
and reports corpus-level edit distance. It is intentionally small and safe; use
the full recipe scorer when exact publication normalization is required.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def read_text(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split(maxsplit=1)
            if len(parts) != 2:
                raise ValueError(f"{path}:{lineno}: expected '<key> <text>'")
            key, text = parts
            if key in rows:
                raise ValueError(f"{path}:{lineno}: duplicate key {key!r}")
            rows[key] = text
    return rows


def units(text: str, mode: str) -> list[str]:
    if mode == "char":
        return [ch for ch in text.replace(" ", "")]
    return text.split()


def edit_counts(ref: list[str], hyp: list[str]) -> tuple[int, int, int]:
    # dp[i][j] = (cost, sub, ins, del)
    dp: list[list[tuple[int, int, int, int]]] = [[(0, 0, 0, 0) for _ in range(len(hyp) + 1)] for _ in range(len(ref) + 1)]
    for i in range(1, len(ref) + 1):
        dp[i][0] = (i, 0, 0, i)
    for j in range(1, len(hyp) + 1):
        dp[0][j] = (j, 0, j, 0)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                best = dp[i - 1][j - 1]
            else:
                cost, sub, ins, dele = dp[i - 1][j - 1]
                best = (cost + 1, sub + 1, ins, dele)
            cost, sub, ins, dele = dp[i][j - 1]
            best = min(best, (cost + 1, sub, ins + 1, dele), key=lambda x: x[0])
            cost, sub, ins, dele = dp[i - 1][j]
            best = min(best, (cost + 1, sub, ins, dele + 1), key=lambda x: x[0])
            dp[i][j] = best
    _, sub, ins, dele = dp[-1][-1]
    return sub, ins, dele


def main() -> int:
    parser = argparse.ArgumentParser(description="Score small WeNet reference/hypothesis text files.")
    parser.add_argument("--reference", required=True, type=Path, help="Reference '<key> <text>' file.")
    parser.add_argument("--hypothesis", required=True, type=Path, help="Hypothesis '<key> <text>' file.")
    parser.add_argument("--unit", choices=["word", "char"], default="word", help="Score as WER or CER.")
    parser.add_argument("--details", action="store_true", help="Include per-utterance edit counts.")
    args = parser.parse_args()

    try:
        refs = read_text(args.reference)
        hyps = read_text(args.hypothesis)
        missing_hyp = sorted(set(refs) - set(hyps))
        extra_hyp = sorted(set(hyps) - set(refs))
        if missing_hyp or extra_hyp:
            raise ValueError(f"key mismatch: missing_hyp={missing_hyp[:10]} extra_hyp={extra_hyp[:10]}")

        totals = {"substitutions": 0, "insertions": 0, "deletions": 0, "reference_units": 0}
        per_utt = []
        for key in refs:
            ref_units = units(refs[key], args.unit)
            hyp_units = units(hyps[key], args.unit)
            sub, ins, dele = edit_counts(ref_units, hyp_units)
            totals["substitutions"] += sub
            totals["insertions"] += ins
            totals["deletions"] += dele
            totals["reference_units"] += len(ref_units)
            if args.details:
                per_utt.append({"key": key, "substitutions": sub, "insertions": ins, "deletions": dele, "reference_units": len(ref_units)})
        errors = totals["substitutions"] + totals["insertions"] + totals["deletions"]
        rate = errors / totals["reference_units"] if totals["reference_units"] else 0.0
        result = {"ok": True, "unit": args.unit, "utterances": len(refs), "errors": errors, "error_rate": rate, **totals}
        if args.details:
            result["details"] = per_utt
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Summarize a quip-miner attempt archive by solution number."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _count_jsonl(path: Path, limit: int | None = None) -> int:
    count = 0
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    count += 1
                    if limit is not None and count >= limit:
                        break
    except OSError:
        return 0
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--solution-number", type=int, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    sol_dir = args.archive.expanduser() / str(args.solution_number)
    result: dict[str, Any] = {"solution_number": args.solution_number, "solution_dir": str(sol_dir), "exists": sol_dir.is_dir()}
    if sol_dir.is_dir():
        result["submission"] = _read_json(sol_dir / "submission.json")
        result["metadata_files"] = []
        for p in sorted(sol_dir.glob("metadata-*.json")):
            data = _read_json(p) or {}
            result["metadata_files"].append({"file": p.name, "n_attempts": data.get("n_attempts"), "best_energy_seen": data.get("best_energy_seen"), "n_submitted": data.get("n_submitted")})
        result["attempt_files"] = [{"file": p.name, "lines": _count_jsonl(p)} for p in sorted(sol_dir.glob("attempts-*.jsonl"))]
        sol_subdir = sol_dir / "solutions"
        result["stored_solution_files"] = len(list(sol_subdir.iterdir())) if sol_subdir.is_dir() else 0
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Solution {args.solution_number}: {'found' if result['exists'] else 'missing'}")
        if result.get("submission"):
            print(f"Submission miner: {result['submission'].get('miner_id')}")
        for rec in result.get("metadata_files", []):
            print(f"{rec['file']}: attempts={rec.get('n_attempts')} submitted={rec.get('n_submitted')} best={rec.get('best_energy_seen')}")
        for rec in result.get("attempt_files", []):
            print(f"{rec['file']}: {rec['lines']} attempt lines")
        if result.get("stored_solution_files") is not None:
            print(f"Stored solution files: {result['stored_solution_files']}")
    return 0 if result["exists"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

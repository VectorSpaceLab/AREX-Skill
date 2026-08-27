#!/usr/bin/env python3
"""Parse Torchreid test logs across split directories.

The parser is deterministic and side-effect-free. It accepts tiny fake logs for
verification and reports missing/incomplete split logs clearly.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional

PATTERNS = {
    "mAP": re.compile(r"\bmAP\s*:\s*([.\deE+-]+)\s*%"),
    "r1": re.compile(r"\bRank-\s*1\s*:\s*([.\deE+-]+)\s*%"),
    "r5": re.compile(r"\bRank-\s*5\s*:\s*([.\deE+-]+)\s*%"),
    "r10": re.compile(r"\bRank-\s*10\s*:\s*([.\deE+-]+)\s*%"),
    "r20": re.compile(r"\bRank-\s*20\s*:\s*([.\deE+-]+)\s*%"),
}


def parse_file(path: Path) -> Dict[str, float]:
    results: Dict[str, float] = {}
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            for key, regex in PATTERNS.items():
                match = regex.search(line)
                if match:
                    results[key] = float(match.group(1))
    return results


def iter_split_dirs(root: Path, pattern: str) -> List[Path]:
    dirs = [p for p in root.glob(pattern) if p.is_dir()]
    if dirs:
        return sorted(dirs, key=lambda p: p.name)
    # Fallback: source utility considered every non-hidden child directory.
    return sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")], key=lambda p: p.name)


def find_log(split_dir: Path, log_glob: str, newest: bool = True) -> Optional[Path]:
    matches = [Path(p) for p in glob.glob(str(split_dir / log_glob))]
    if not matches:
        return None
    if newest:
        return max(matches, key=lambda p: p.stat().st_mtime)
    return sorted(matches)[0]


def summarize(values: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
    summary: Dict[str, Dict[str, float]] = {}
    for key, vals in values.items():
        if not vals:
            continue
        item = {"count": float(len(vals)), "mean": sum(vals) / float(len(vals))}
        if len(vals) > 1:
            item["stdev"] = statistics.stdev(vals)
        else:
            item["stdev"] = 0.0
        summary[key] = item
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse Torchreid test.log* files under split directories and average mAP/CMC metrics.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("directory", help="Root directory containing split subdirectories.")
    parser.add_argument("--split-pattern", default="split_*", help="Glob for split directories; falls back to all non-hidden directories if none match.")
    parser.add_argument("--log-glob", default="test.log*", help="Glob used inside each split directory.")
    parser.add_argument("--oldest", action="store_true", help="Use the lexicographically first matching log instead of newest by mtime.")
    parser.add_argument("--strict", action="store_true", help="Fail if any split is missing a log or required fields.")
    parser.add_argument("--require", nargs="+", default=["mAP", "r1", "r5", "r10", "r20"], choices=sorted(PATTERNS), help="Metrics required for each parsed log.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(os.path.expanduser(args.directory)).resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: directory does not exist or is not a directory: {root}", file=sys.stderr)
        return 2

    split_dirs = iter_split_dirs(root, args.split_pattern)
    if not split_dirs:
        print(f"ERROR: no split directories found under {root}", file=sys.stderr)
        return 2

    values: Dict[str, List[float]] = {key: [] for key in PATTERNS}
    parsed: List[Dict[str, object]] = []
    missing: List[str] = []
    incomplete: List[str] = []

    for split_dir in split_dirs:
        log_path = find_log(split_dir, args.log_glob, newest=not args.oldest)
        if log_path is None:
            message = f"{split_dir.name}: no log matching {args.log_glob!r}"
            missing.append(message)
            continue
        results = parse_file(log_path)
        absent = [key for key in args.require if key not in results]
        if absent:
            incomplete.append(f"{split_dir.name}: {log_path.name} missing {', '.join(absent)}")
        for key, value in results.items():
            values[key].append(value)
        parsed.append({"split": split_dir.name, "log": str(log_path), "metrics": results})

    summary = summarize(values)
    status = {
        "root": str(root),
        "num_split_dirs": len(split_dirs),
        "num_logs_parsed": len(parsed),
        "missing": missing,
        "incomplete": incomplete,
        "summary": summary,
        "parsed": parsed,
    }

    if args.json:
        print(json.dumps(status, indent=2, sort_keys=False))
    else:
        print(f"Parsed {len(parsed)} log(s) from {len(split_dirs)} split directorie(s) under {root}")
        for item in parsed:
            print(f"Parsing {item['log']}")
        if missing:
            print("\nMissing logs:")
            for item in missing:
                print(f"  - {item}")
        if incomplete:
            print("\nIncomplete logs:")
            for item in incomplete:
                print(f"  - {item}")
        print("\nAverage results:")
        if not summary:
            print("  No metrics were parsed.")
        for key in ["mAP", "r1", "r5", "r10", "r20"]:
            if key in summary:
                item = summary[key]
                print(f"  {key}: {item['mean']:.1f} (n={int(item['count'])}, stdev={item['stdev']:.2f})")

    if not parsed:
        return 2
    if args.strict and (missing or incomplete):
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

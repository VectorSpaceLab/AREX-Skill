#!/usr/bin/env python
"""Run SHISO with the import shim required by this package.

The repository's SHISO package uses a non-relative import. This helper locates
the installed `logparser/SHISO` directory, adds it to `sys.path`, and then runs a
small SHISO parse or a user-supplied log file.

Example:
    python scripts/run_shiso_with_import_shim.py
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


def _bootstrap_repo_root() -> None:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "setup.py").exists() and (candidate / "logparser").is_dir():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Could not locate the repository root for Logparser")


DEFAULT_SAMPLE = """2026-01-01 12:00:00 INFO start service
2026-01-01 12:00:01 INFO start worker
2026-01-01 12:00:02 INFO stop worker
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, help="log file to parse; a tiny sample is used when omitted")
    parser.add_argument("--log-name", default="sample.log", help="log file name when creating a tiny sample")
    parser.add_argument("--output-dir", type=Path, default=Path("./shiso_result/"), help="output directory")
    parser.add_argument("--log-format", default="<Date> <Time> <Level> <Content>", help="SHISO log format string")
    parser.add_argument("--max-child-num", type=int, default=4)
    parser.add_argument("--merge-threshold", type=float, default=0.1)
    parser.add_argument("--format-lookup-threshold", type=float, default=0.3)
    parser.add_argument("--super-format-threshold", type=float, default=0.85)
    parser.add_argument("--regex", action="append", default=[], help="regex preprocessing rule; may be repeated")
    return parser


def main() -> int:
    _bootstrap_repo_root()
    import logparser

    shiso_dir = Path(logparser.__file__).resolve().parent / "SHISO"
    sys.path.insert(0, str(shiso_dir))
    from logparser.SHISO import LogParser  # pylint: disable=import-outside-toplevel

    args = build_parser().parse_args()

    if args.input_file is None:
        root = Path(tempfile.mkdtemp(prefix="logparser-shiso-"))
        input_dir = root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        log_name = args.log_name
        (input_dir / log_name).write_text(DEFAULT_SAMPLE, encoding="utf-8")
    else:
        input_dir = args.input_file.parent
        log_name = args.input_file.name

    args.output_dir.mkdir(parents=True, exist_ok=True)
    parser = LogParser(
        args.log_format,
        indir=str(input_dir),
        outdir=str(args.output_dir),
        maxChildNum=args.max_child_num,
        mergeThreshold=args.merge_threshold,
        formatLookupThreshold=args.format_lookup_threshold,
        superFormatThreshold=args.super_format_threshold,
        rex=args.regex,
    )
    parser.parse(log_name)

    print(args.output_dir / f"{log_name}_structured.csv")
    print(args.output_dir / f"{log_name}_templates.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

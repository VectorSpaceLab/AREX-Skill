#!/usr/bin/env python
"""Run a tiny Drain parse smoke.

This script is safe to run from any directory. It creates a small sample log
when no input file is supplied, runs Drain, and reports the output files.

Example:
    python scripts/parse_tiny_drain.py
    python scripts/parse_tiny_drain.py --input-file sample.log --output-dir out/
"""

from __future__ import annotations

import argparse
import importlib
import tempfile
from pathlib import Path


def _load_log_parser():
    """Load Drain from the published ``logparser3`` package."""
    try:
        module = importlib.import_module("logparser.Drain")
    except ModuleNotFoundError as exc:
        if exc.name not in {"logparser", "logparser.Drain"}:
            raise
        raise RuntimeError("Drain is unavailable; install logparser3") from exc

    try:
        return module.LogParser
    except AttributeError as exc:
        raise RuntimeError("The installed logparser package does not provide Drain.LogParser") from exc


DEFAULT_SAMPLE = """2026-01-01 12:00:00 INFO start service
2026-01-01 12:00:01 INFO start worker
2026-01-01 12:00:02 INFO stop worker
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, help="log file to parse; a tiny sample is used when omitted")
    parser.add_argument("--input-dir", type=Path, help="directory containing the log file; defaults to the file's parent or a temp dir")
    parser.add_argument("--log-name", default="sample.log", help="log file name when creating a tiny sample")
    parser.add_argument("--output-dir", type=Path, default=Path("./drain_result/"), help="output directory for parsed CSVs")
    parser.add_argument("--log-format", default="<Date> <Time> <Level> <Content>", help="Drain log format string")
    parser.add_argument("--depth", type=int, default=4, help="Drain tree depth")
    parser.add_argument("--st", type=float, default=0.5, help="Drain similarity threshold")
    parser.add_argument("--regex", action="append", default=[], help="regex preprocessing rule; may be repeated")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    LogParser = _load_log_parser()

    if args.input_file is None:
        temp_root = Path(tempfile.mkdtemp(prefix="logparser-drain-"))
        input_dir = temp_root / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        log_path = input_dir / args.log_name
        log_path.write_text(DEFAULT_SAMPLE, encoding="utf-8")
        log_name = args.log_name
    else:
        log_path = args.input_file
        log_name = args.log_name if args.log_name else log_path.name
        input_dir = args.input_dir or log_path.parent

    args.output_dir.mkdir(parents=True, exist_ok=True)
    parser = LogParser(
        args.log_format,
        indir=str(input_dir),
        outdir=str(args.output_dir),
        depth=args.depth,
        st=args.st,
        rex=args.regex,
    )
    parser.parse(log_name)

    structured = args.output_dir / f"{log_name}_structured.csv"
    templates = args.output_dir / f"{log_name}_templates.csv"
    print(structured)
    print(templates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

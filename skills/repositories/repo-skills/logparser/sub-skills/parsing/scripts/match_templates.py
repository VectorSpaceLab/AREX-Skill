#!/usr/bin/env python
"""Match logs against an existing templates CSV.

When no explicit input/template pair is supplied, this script generates a tiny
Drain parse first and then reuses the resulting templates file for matching.
That makes it a safe end-to-end smoke for the parsing + logmatch path.

Example:
    python scripts/match_templates.py
    python scripts/match_templates.py --input-file sample.log --template-file sample.log_templates.csv
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


_bootstrap_repo_root()

from logparser.Drain import LogParser
from logparser.logmatch import RegexMatch
from logparser.utils import logloader

DEFAULT_SAMPLE = """2026-01-01 12:00:00 INFO start service
2026-01-01 12:00:01 INFO start worker
2026-01-01 12:00:02 INFO stop worker
"""


def _safe_generate_logformat_regex(self, logformat):
    headers = []
    splitters = logloader.re.split(r"(<[^<>]+>)", logformat)
    regex = ""
    for k in range(len(splitters)):
        if k % 2 == 0:
            splitter = logloader.re.sub(" +", r"\\s+", splitters[k])
            regex += splitter
        else:
            header = splitters[k].strip("<").strip(">")
            regex += "(?P<%s>.*?)" % header
            headers.append(header)
    regex = logloader.re.compile("^" + regex + "$")
    return headers, regex


logloader.LogLoader._generate_logformat_regex = _safe_generate_logformat_regex


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, help="log file to match")
    parser.add_argument("--template-file", type=Path, help="templates CSV to reuse")
    parser.add_argument("--input-dir", type=Path, help="directory containing the log file")
    parser.add_argument("--output-dir", type=Path, default=Path("./match_result/"), help="output directory for the match results")
    parser.add_argument("--log-name", default="sample.log", help="log file name when a tiny sample is generated")
    parser.add_argument("--log-format", default="<Date> <Time> <Level> <Content>", help="log format string shared by Drain and RegexMatch")
    parser.add_argument("--n-workers", type=int, default=1, help="parallel workers for RegexMatch")
    parser.add_argument("--depth", type=int, default=4, help="Drain tree depth when the script auto-generates a tiny sample")
    parser.add_argument("--st", type=float, default=0.5, help="Drain similarity threshold when the script auto-generates a tiny sample")
    parser.add_argument("--regex", action="append", default=[], help="regex preprocessing rule; may be repeated")
    return parser


def make_tiny_parse(root: Path, log_name: str, log_format: str, depth: int, st: float, regex: list[str]):
    input_dir = root / "input"
    output_dir = root / "parse"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = input_dir / log_name
    log_path.write_text(DEFAULT_SAMPLE, encoding="utf-8")
    parser = LogParser(log_format, indir=str(input_dir), outdir=str(output_dir), depth=depth, st=st, rex=regex)
    parser.parse(log_name)
    return log_path, output_dir / f"{log_name}_templates.csv"


def main() -> int:
    args = build_parser().parse_args()
    root = Path(tempfile.mkdtemp(prefix="logparser-match-"))

    if args.input_file is None or args.template_file is None:
        log_path, template_path = make_tiny_parse(root, args.log_name, args.log_format, args.depth, args.st, args.regex)
        input_file = log_path
        template_file = template_path
    else:
        input_file = args.input_file
        template_file = args.template_file

    match_out = args.output_dir
    match_out.mkdir(parents=True, exist_ok=True)
    matcher = RegexMatch(outdir=str(match_out), n_workers=args.n_workers, logformat=args.log_format)
    matcher.match(str(input_file), str(template_file))

    print(match_out / f"{Path(input_file).name}_structured.csv")
    print(match_out / f"{Path(input_file).name}_templates.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

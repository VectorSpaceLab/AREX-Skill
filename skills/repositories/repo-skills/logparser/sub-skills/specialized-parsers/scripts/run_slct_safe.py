#!/usr/bin/env python
"""Compile and run SLCT with safer GCC flags.

The repository's legacy SLCT wrapper compiles a C helper with a hard-coded
command. On modern GCC, warnings can stop that command. This helper creates a
temporary working layout, compiles with `-Wno-error`, and then invokes the
installed `logparser.SLCT.LogParser` against either a tiny fixture or a supplied
log file.

Example:
    python scripts/run_slct_safe.py
    python scripts/run_slct_safe.py --input-file sample.log --support 2
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
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


@contextmanager
def pushd(path: Path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, help="log file to parse; a tiny sample is used when omitted")
    parser.add_argument("--log-name", default="sample.log", help="log file name when creating a tiny sample")
    parser.add_argument("--output-dir", type=Path, default=Path("./slct_result/"), help="output directory")
    parser.add_argument("--log-format", default="<Date> <Time> <Level> <Content>", help="SLCT log format string")
    parser.add_argument("--support", type=int, default=1, help="minimum support threshold")
    parser.add_argument("--no-para-j", action="store_true", help="disable SLCT -j parameter")
    parser.add_argument("--save-log", action="store_true", help="keep SLCT intermediate logs when supported")
    parser.add_argument("--gcc", default="gcc", help="GCC executable")
    parser.add_argument("--regex", action="append", default=[], help="regex preprocessing rule; may be repeated")
    return parser


def compile_slct(source_c: Path, work: Path, gcc: str) -> None:
    src_dir = work / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    for candidate in source_c.parent.iterdir():
        if candidate.name.startswith("cslct."):
            shutil.copy2(candidate, src_dir / candidate.name)
    command = [gcc, "-O2", "-Wno-error", "-o", str(src_dir / "slct"), str(src_dir / "cslct.c")]
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(proc.returncode)


def main() -> int:
    _bootstrap_repo_root()
    import logparser

    args = build_parser().parse_args()
    package_dir = Path(logparser.__file__).resolve().parent
    source_c = package_dir / "SLCT" / "src" / "cslct.c"
    if not source_c.exists():
        raise SystemExit(f"Cannot find installed SLCT source file: {source_c}")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="logparser-slct-") as tmp:
        root = Path(tmp)
        work = root / "work"
        work.mkdir(parents=True, exist_ok=True)
        sentinel_dir = root / "SLCT"
        sentinel_dir.mkdir(parents=True, exist_ok=True)
        (sentinel_dir / "slct").write_text("sentinel", encoding="utf-8")

        if args.input_file is None:
            input_dir = root / "input"
            input_dir.mkdir(parents=True, exist_ok=True)
            log_name = args.log_name
            (input_dir / log_name).write_text(DEFAULT_SAMPLE, encoding="utf-8")
        else:
            input_file = args.input_file.resolve()
            input_dir = input_file.parent
            log_name = input_file.name

        compile_slct(source_c, work, args.gcc)

        from logparser.SLCT import LogParser  # pylint: disable=import-outside-toplevel

        parser = LogParser(
            str(input_dir),
            str(output_dir),
            args.log_format,
            support=args.support,
            para_j=not args.no_para_j,
            saveLog=args.save_log,
            rex=args.regex,
        )
        with pushd(work):
            parser.parse(log_name)

    print(output_dir / f"{log_name}_structured.csv")
    print(output_dir / f"{log_name}_templates.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

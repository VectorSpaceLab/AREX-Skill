#!/usr/bin/env python3
"""Run a no-network fg-data-profiling CLI smoke test on a tiny CSV.

Examples:
  python cli_smoke.py
  python cli_smoke.py --command pandas_profiling --keep-output /tmp/fg-cli-smoke
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate data_profiling/pandas_profiling CLI on a tiny generated CSV.")
    parser.add_argument("--command", default="data_profiling", choices=["data_profiling", "pandas_profiling"], help="CLI command to test.")
    parser.add_argument("--keep-output", help="Directory to keep generated CSV/report; default uses a temporary directory.")
    args = parser.parse_args()

    exe = shutil.which(args.command)
    if not exe:
        print(f"Missing executable: {args.command}. Install fg-data-profiling in this environment or fix PATH.", file=sys.stderr)
        return 2

    if args.keep_output:
        workdir = Path(args.keep_output).expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        cleanup = None
    else:
        cleanup = tempfile.TemporaryDirectory(prefix="fg-cli-smoke-")
        workdir = Path(cleanup.name)

    try:
        csv_path = workdir / "tiny.csv"
        report_path = workdir / "tiny-profile.html"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["amount", "segment"])
            writer.writeheader()
            writer.writerows([
                {"amount": "10", "segment": "retail"},
                {"amount": "20", "segment": "enterprise"},
                {"amount": "20", "segment": "enterprise"},
            ])

        proc = subprocess.run(
            [exe, "--silent", "--minimal", str(csv_path), str(report_path)],
            text=True,
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            print(proc.stdout, file=sys.stdout)
            print(proc.stderr, file=sys.stderr)
            return proc.returncode
        if not report_path.exists() or report_path.stat().st_size == 0:
            print(f"CLI completed but report was not created: {report_path}", file=sys.stderr)
            return 3
        print(f"CLI smoke passed with {args.command}; report={report_path}; size={report_path.stat().st_size}")
        return 0
    finally:
        if cleanup is not None:
            cleanup.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())

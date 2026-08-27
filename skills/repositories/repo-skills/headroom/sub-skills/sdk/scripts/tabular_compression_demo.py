#!/usr/bin/env python3
"""Self-contained Headroom spreadsheet/table compression demo.

Creates a small workbook in a temporary directory, calls
`compress_spreadsheet`, and prints the resulting token metrics. The workbook is
removed unless `--write-dir` is supplied. The demo uses the optional
`spreadsheet` extra and disables Kompress so it stays local and deterministic.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local Headroom spreadsheet compression demo.")
    parser.add_argument("--write-dir", type=Path, default=None, help="Keep generated workbook and report under this directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON metrics.")
    return parser.parse_args()


def build_workbook(path: Path) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "events"
    sheet.append(["id", "service", "status", "message"])
    for idx in range(60):
        sheet.append([idx, "api", "ok", "normal background event"])
    sheet.append([60, "payments", "ERROR", "payment-db connection refused"])
    sheet.append([61, "auth", "ERROR", "token validation failed"])
    workbook.save(path)


def main() -> int:
    args = parse_args()
    if args.write_dir:
        args.write_dir.mkdir(parents=True, exist_ok=True)
        root = args.write_dir
        cleanup = False
    else:
        temp = tempfile.TemporaryDirectory(prefix="headroom-tabular-demo-")
        root = Path(temp.name)
        cleanup = True

    workbook_path = root / "headroom-demo.xlsx"
    build_workbook(workbook_path)

    from headroom import compress_spreadsheet

    result = compress_spreadsheet(
        str(workbook_path),
        model="gpt-4o",
        kompress_model="disabled",
        min_tokens_to_compress=0,
        protect_recent=0,
    )
    report = {
        "workbook": str(workbook_path) if args.write_dir else "temporary workbook",
        "tokens_before": result.tokens_before,
        "tokens_after": result.tokens_after,
        "tokens_saved": result.tokens_saved,
        "transforms_applied": result.transforms_applied,
        "temporary_files_removed": cleanup,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Headroom tabular compression demo")
        print(f"tokens: {result.tokens_before} -> {result.tokens_after}")
        print(f"saved: {result.tokens_saved}")
        print(f"transforms: {', '.join(result.transforms_applied) or 'none'}")
        if args.write_dir:
            print(f"workbook: {workbook_path}")

    if cleanup:
        temp.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

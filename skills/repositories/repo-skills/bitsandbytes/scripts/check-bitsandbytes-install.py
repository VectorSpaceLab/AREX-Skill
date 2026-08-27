#!/usr/bin/env python3
"""Root bitsandbytes install/backend check.

This wrapper runs the bundled installation-diagnostics backend report from the
repo skill tree. It is read-only: no downloads, package installs, kernel runs,
or environment mutation.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


def load_backend_report():
    script = Path(__file__).resolve().parents[1] / "sub-skills" / "installation-diagnostics" / "scripts" / "backend-report.py"
    spec = importlib.util.spec_from_file_location("bitsandbytes_skill_backend_report", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load bundled backend report helper at {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a read-only bitsandbytes import/backend diagnostic report.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--include-device-names",
        action="store_true",
        help="Include CUDA device names. Omit this when sharing reports publicly if device names are sensitive.",
    )
    args = parser.parse_args(argv)

    helper = load_backend_report()
    report = helper.build_report(include_device_names=args.include_device_names)
    if args.json:
        import json

        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        helper.print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

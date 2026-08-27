#!/usr/bin/env python3
"""List or inspect Torch-TensorRT CI suites from the local checkout.

This helper is read-only. Pass --repo-root explicitly when running outside the
skill directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Torch-TensorRT CI suite definitions.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="path to the Torch-TensorRT checkout")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()

    suites_py = args.repo_root / "tests" / "ci" / "suites.py"
    result: Dict[str, Any] = {"repo_root": str(args.repo_root), "suites_py": str(suites_py), "exists": suites_py.exists()}
    if suites_py.exists():
        text = suites_py.read_text(encoding="utf-8")
        import re

        names = []
        for match in re.finditer(r"Suite\(\s*\n\s*[\"']([^\"']+)[\"']", text):
            names.append(match.group(1))
        result["suite_names"] = names[:200]
        result["suite_count"] = len(names)
        result["line_count"] = len(text.splitlines())
    else:
        result["suite_names"] = []
        result["suite_count"] = 0
        result["line_count"] = 0
        result["note"] = "tests/ci/suites.py not found under the provided repository root"

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check the installed img2dataset package and optional backend availability.

This helper is intentionally lightweight and safe by default. It verifies the
public package, the main download signature, and optional module availability
without depending on the original repository checkout.

Examples:
    python scripts/check_img2dataset_env.py
    python scripts/check_img2dataset_env.py --json --check-cli
    python scripts/check_img2dataset_env.py --show-paths
"""

from __future__ import annotations

import argparse
import inspect
import json
import shutil
import subprocess
import sys
from importlib import metadata, util


def _module_status(name: str) -> dict:
    spec = util.find_spec(name)
    return {
        "name": name,
        "available": spec is not None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the installed img2dataset package and optional backends.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    parser.add_argument("--check-cli", action="store_true", help="Run a safe img2dataset help check.")
    parser.add_argument("--show-paths", action="store_true", help="Include module origin paths in the report.")
    args = parser.parse_args()

    report: dict = {"package": {}, "optional": [], "checks": []}

    try:
        import img2dataset
        from img2dataset import download
    except Exception as exc:  # pragma: no cover - diagnostic helper
        report["package"] = {"installed": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("img2dataset import failed:", f"{type(exc).__name__}: {exc}")
        return 1

    report["package"] = {
        "installed": True,
        "distribution": metadata.version("img2dataset"),
        "download_signature": str(inspect.signature(download)),
    }
    if args.show_paths:
        report["package"]["module_path"] = getattr(img2dataset, "__file__", None)

    optional_names = ["pyspark", "ray", "tensorflow", "tensorflow_io", "fastapi", "uvicorn", "wandb", "webdataset"]
    report["optional"] = [_module_status(name) for name in optional_names]

    if args.check_cli:
        cli = shutil.which("img2dataset")
        if cli is None:
            cmd = [sys.executable, "-m", "img2dataset.main", "--", "--help"]
        else:
            cmd = [cli, "--help"]
        completed = subprocess.run(cmd, capture_output=True, text=True)
        report["checks"].append(
            {
                "name": "cli-help",
                "command": cmd,
                "returncode": completed.returncode,
                "stdout_head": completed.stdout.splitlines()[:10],
                "stderr_head": completed.stderr.splitlines()[:10],
            }
        )
        if completed.returncode != 0:
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print("CLI help failed:")
                print(completed.stdout)
                print(completed.stderr, file=sys.stderr)
            return completed.returncode

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"img2dataset {report['package']['distribution']}")
        print(report["package"]["download_signature"])
        for item in report["optional"]:
            print(f"{item['name']}: {'present' if item['available'] else 'missing'}")
        if args.check_cli:
            print("cli-help: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

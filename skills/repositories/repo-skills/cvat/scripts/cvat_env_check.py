#!/usr/bin/env python3
"""Safe CVAT package/CLI environment check.

The script imports public CVAT SDK/CLI packages and optionally runs cvat-cli --help.
It does not contact a CVAT server and does not read credentials.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module: str) -> dict[str, str]:
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        return {"module": module, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    return {"module": module, "status": "ok", "file": getattr(mod, "__file__", "built-in")}


def cli_help(executable: str) -> dict[str, object]:
    path = shutil.which(executable)
    if not path:
        return {"executable": executable, "status": "missing"}
    proc = subprocess.run([path, "--help"], text=True, capture_output=True, timeout=20, check=False)
    return {
        "executable": executable,
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "first_stdout_line": proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "",
        "stderr": proc.stderr.strip().splitlines()[:3],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-cli-help", action="store_true")
    parser.add_argument("--cli", default="cvat-cli")
    args = parser.parse_args()

    report = {
        "python": sys.version,
        "distributions": {
            "cvat-sdk": dist_version("cvat-sdk"),
            "cvat-cli": dist_version("cvat-cli"),
        },
        "imports": [
            import_status("cvat_sdk"),
            import_status("cvat_sdk.core.client"),
            import_status("cvat_sdk.auto_annotation"),
            import_status("cvat_sdk.datasets"),
            import_status("cvat_cli.__main__"),
        ],
    }
    if not args.skip_cli_help:
        report["cli_help"] = cli_help(args.cli)
    print(json.dumps(report, indent=2, sort_keys=True))
    failed = any(item["status"] != "ok" for item in report["imports"])
    if report.get("cli_help", {}).get("status") == "failed":
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

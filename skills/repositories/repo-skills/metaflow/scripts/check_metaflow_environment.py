#!/usr/bin/env python3
"""Check a public Metaflow installation without reading a source checkout.

Example:
  python check_metaflow_environment.py --json
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Metaflow import, metadata, CLI, and username readiness.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--require-username", action="store_true", help="Fail if no username-like environment variable is set.")
    args = parser.parse_args()

    result = {"ok": True, "checks": {}, "warnings": []}
    try:
        import metaflow
        result["checks"]["import"] = {"status": "pass", "version": getattr(metaflow, "__version__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["ok"] = False
        result["checks"]["import"] = {"status": "fail", "error": repr(exc)}

    try:
        dist_version = metadata.version("metaflow")
        eps = metadata.distribution("metaflow").entry_points
        scripts = sorted(ep.name for ep in eps if ep.group == "console_scripts")
        result["checks"]["metadata"] = {"status": "pass", "version": dist_version, "console_scripts": scripts}
    except Exception as exc:  # pragma: no cover
        result["ok"] = False
        result["checks"]["metadata"] = {"status": "fail", "error": repr(exc)}

    cli = shutil.which("metaflow")
    result["checks"]["metaflow_cli"] = {"status": "pass" if cli else "warn", "found": bool(cli)}
    if cli:
        proc = subprocess.run([cli, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        result["checks"]["metaflow_cli"]["help_exit_code"] = proc.returncode
        if proc.returncode != 0:
            result["ok"] = False
            result["checks"]["metaflow_cli"]["stderr"] = proc.stderr[-500:]

    username_keys = ["METAFLOW_USER", "USERNAME", "USER", "LOGNAME"]
    visible = {key: bool(os.environ.get(key)) for key in username_keys}
    result["checks"]["username"] = {"status": "pass" if any(visible.values()) else "warn", "visible_keys": visible}
    if args.require_username and not any(visible.values()):
        result["ok"] = False
        result["warnings"].append("Set USERNAME or METAFLOW_USER before running flow CLIs in automation.")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, info in result["checks"].items():
            print(f"{name}: {info['status']}")
        for warning in result["warnings"]:
            print(f"warning: {warning}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe LM Evaluation Harness installation checker.

This helper checks package metadata, lightweight imports, CLI help, and lazy model
registry aliases without importing concrete heavy backend classes directly.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys


def run_help(command: str) -> dict[str, object]:
    exe = shutil.which(command)
    if not exe:
        return {"command": command, "found": False, "ok": False, "error": "not on PATH"}
    proc = subprocess.run([exe, "--help"], text=True, capture_output=True, timeout=20)
    return {
        "command": command,
        "found": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_first_line": proc.stdout.splitlines()[0] if proc.stdout else "",
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check lm_eval install, CLI help, and lazy registry aliases.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    report: dict[str, object] = {"ok": True, "checks": {}}
    try:
        version = metadata.version("lm_eval")
        report["checks"]["distribution"] = {"ok": True, "version": version}
    except metadata.PackageNotFoundError as exc:
        report["ok"] = False
        report["checks"]["distribution"] = {"ok": False, "error": str(exc)}

    try:
        import lm_eval  # noqa: F401

        report["checks"]["import_lm_eval"] = {"ok": True}
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["ok"] = False
        report["checks"]["import_lm_eval"] = {"ok": False, "error": repr(exc)}

    report["checks"]["cli"] = [run_help("lm-eval"), run_help("lm_eval")]
    if not any(item.get("ok") for item in report["checks"]["cli"]):
        report["ok"] = False

    try:
        import lm_eval.models  # noqa: F401
        from lm_eval.api import registry

        report["checks"]["model_registry"] = {
            "ok": True,
            "aliases": sorted(registry.MODEL_REGISTRY.keys()),
            "note": "Registry aliases do not prove optional backend dependencies are installed.",
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["checks"]["model_registry"] = {"ok": False, "error": repr(exc)}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"lm_eval install ok: {report['ok']}")
        for name, value in report["checks"].items():
            print(f"{name}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

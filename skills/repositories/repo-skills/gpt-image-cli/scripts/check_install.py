#!/usr/bin/env python3
"""Safe no-network install check for gpt-image-cli.

This script verifies the package import, distribution metadata, console command
availability, and CLI help/parser surface. It never calls the OpenAI Images API
and never prints API-key values.

Examples:
  python scripts/check_install.py
  python scripts/check_install.py --json
  python scripts/check_install.py --skip-cli-help
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any


def _run(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        cp = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "cmd": cmd,
            "returncode": cp.returncode,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"cmd": cmd, "returncode": None, "error": f"{type(exc).__name__}: {exc}"}


def check(skip_cli_help: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": True,
        "checks": {},
        "warnings": [],
        "notes": [],
    }

    try:
        dist_version = metadata.version("gpt-image-cli")
        dist_meta = metadata.metadata("gpt-image-cli")
        eps = [f"{ep.name}:{ep.value}" for ep in metadata.entry_points(group="console_scripts") if ep.name == "gpt-image"]
        result["checks"]["distribution"] = {
            "ok": True,
            "name": dist_meta.get("Name"),
            "version": dist_version,
            "requires_python": dist_meta.get("Requires-Python"),
            "console_scripts": eps,
        }
        if not eps:
            result["ok"] = False
            result["warnings"].append("Console script 'gpt-image' is not registered in this environment.")
    except metadata.PackageNotFoundError:
        result["ok"] = False
        result["checks"]["distribution"] = {"ok": False, "error": "gpt-image-cli distribution not found"}

    try:
        pkg = importlib.import_module("gpt_image_cli")
        cli = importlib.import_module("gpt_image_cli.cli")
        result["checks"]["import"] = {
            "ok": True,
            "module": pkg.__name__,
            "default_model": getattr(cli, "DEFAULT_MODEL", None),
            "default_size": getattr(cli, "DEFAULT_SIZE", None),
            "default_moderation": getattr(cli, "DEFAULT_MODERATION", None),
            "portrait_size": cli.resolve_size("portrait") if hasattr(cli, "resolve_size") else None,
        }
    except Exception as exc:
        result["ok"] = False
        result["checks"]["import"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    executable = shutil.which("gpt-image")
    result["checks"]["path"] = {"ok": bool(executable), "gpt_image_executable_found": bool(executable)}
    if not executable:
        result["warnings"].append("'gpt-image' is not on PATH; try 'python -m gpt_image_cli.cli --help' in the target environment.")

    if not skip_cli_help:
        cmd = [executable, "--help"] if executable else [sys.executable, "-m", "gpt_image_cli.cli", "--help"]
        help_result = _run(cmd)
        help_ok = help_result.get("returncode") == 0 and "--prompt" in help_result.get("stdout", "")
        result["checks"]["cli_help"] = {"ok": help_ok, **help_result}
        if not help_ok:
            result["ok"] = False

    result["checks"]["api_key"] = {
        "ok": True,
        "OPENAI_API_KEY_present": bool(os.environ.get("OPENAI_API_KEY")),
        "value_printed": False,
    }
    if not os.environ.get("OPENAI_API_KEY"):
        result["notes"].append("OPENAI_API_KEY is not set in the process environment; real image calls will fail unless dotenv files or a host runtime provide it.")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe no-network install check for gpt-image-cli.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of a concise text summary.")
    parser.add_argument("--skip-cli-help", action="store_true", help="Skip invoking CLI --help.")
    args = parser.parse_args()

    result = check(skip_cli_help=args.skip_cli_help)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "ok" if result["ok"] else "failed"
        print(f"gpt-image-cli install check: {status}")
        for name, payload in result["checks"].items():
            print(f"- {name}: {'ok' if payload.get('ok') else 'problem'}")
        for warning in result["warnings"]:
            print(f"warning: {warning}", file=sys.stderr)
        for note in result["notes"]:
            print(f"note: {note}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Safe Langchain-Chatchat package/environment probe.

This helper verifies import names, selected distribution metadata, optional
package presence, and the `chatchat` CLI help surface. It does not start a
server, call a model provider, rebuild vectors, or touch user knowledge-base
files.

Example:
  python chatchat_env_probe.py --json
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version


def dist_version(name: str):
    try:
        return version(name)
    except PackageNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover
        return f"ERROR: {type(exc).__name__}: {exc}"


def import_status(name: str):
    try:
        module = importlib.import_module(name)
        return {
            "ok": True,
            "version": getattr(module, "__version__", None),
            "exports": sorted(getattr(module, "__all__", [])) if hasattr(module, "__all__") else None,
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def cli_help(command: list[str], timeout: float, env: dict[str, str]):
    exe = shutil.which(command[0])
    if not exe:
        return {"ok": False, "error": f"{command[0]!r} not found on PATH"}
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_first_lines": proc.stdout.splitlines()[:20],
            "stderr_first_lines": proc.stderr.splitlines()[:20],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Langchain-Chatchat imports and CLI without starting services.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip `chatchat --help` checks.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Timeout in seconds for each CLI help command.")
    parser.add_argument("--chatchat-root", help="Optional initialized or disposable CHATCHAT_ROOT for imports and CLI help. Defaults to a temporary root.")
    args = parser.parse_args()

    temp_ctx = None
    if args.chatchat_root:
        root = Path(args.chatchat_root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        root_source = "provided"
    else:
        temp_ctx = tempfile.TemporaryDirectory(prefix="chatchat-env-probe-")
        root = Path(temp_ctx.name)
        root_source = "temporary"
    os.environ["CHATCHAT_ROOT"] = str(root)
    cli_env = dict(os.environ)

    report = {
        "python": sys.version.split()[0],
        "chatchat_root_source": root_source,
        "distributions": {
            "langchain-chatchat": dist_version("langchain-chatchat"),
            "open_chatcaht": dist_version("open_chatcaht"),
            "open-langchain-chatchat": dist_version("open-langchain-chatchat"),
        },
        "imports": {
            "chatchat": import_status("chatchat"),
            "langchain_chatchat": import_status("langchain_chatchat"),
            "open_chatcaht": import_status("open_chatcaht"),
            "xinference_client": import_status("xinference_client"),
        },
        "cli": {},
        "notes": [
            "open_chatcaht is intentionally spelled as inspected in this repository.",
            "xinference_client is optional unless the Chatchat environment must auto-detect Xinference models.",
        ],
    }

    if not args.skip_cli:
        for cmd in (["chatchat", "--help"], ["chatchat", "init", "--help"], ["chatchat", "kb", "--help"], ["chatchat", "start", "--help"]):
            report["cli"][" ".join(cmd[:-1])] = cli_help(list(cmd), args.timeout, cli_env)

    failed = []
    for name in ["chatchat", "langchain_chatchat"]:
        if not report["imports"][name]["ok"]:
            failed.append(f"import {name}")
    if not args.skip_cli:
        for name, result in report["cli"].items():
            if not result.get("ok"):
                failed.append(f"CLI {name} --help")
    report["ok"] = not failed
    report["failed_checks"] = failed

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Langchain-Chatchat probe: {'OK' if report['ok'] else 'FAILED'}")
        for name, result in report["imports"].items():
            print(f"import {name}: {'ok' if result['ok'] else result['error']}")
        if not args.skip_cli:
            for name, result in report["cli"].items():
                print(f"{name} --help: {'ok' if result.get('ok') else result.get('error', result.get('returncode'))}")
        if failed:
            print("Failed checks:", ", ".join(failed), file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

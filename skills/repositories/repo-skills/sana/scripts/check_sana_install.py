#!/usr/bin/env python3
"""Safe Sana install smoke check.

Imports public Sana modules and, unless --skip-cli is set, runs the --help
parsers for the public console scripts. This helper does not download weights,
load checkpoints, start services, run generation, or launch training.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

# Prefer an import-only inspection path over optional fused-kernel paths.
os.environ.setdefault("DISABLE_XFORMERS", "1")
os.environ.setdefault("DISABLE_FLASH_ATTN", "1")

IMPORT_TARGETS = [
    "sana.cli.run",
    "sana.cli.upload2hf",
    "sana.tools.download",
    "diffusion",
    "diffusion.model.builder",
    "diffusion.data.builder",
    "app.sana_pipeline",
    "app.sana_sprint_pipeline",
    "app.sana_controlnet_pipeline",
]

CLI_TARGETS = [
    ("sana-run", "sana.cli.run"),
    ("sana-upload", "sana.cli.upload2hf"),
]


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def preview(text: str, max_lines: int = 8) -> list[str]:
    return [line for line in text.splitlines()[:max_lines] if line.strip()]


def check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {
            "name": name,
            "ok": True,
            "module_file": getattr(module, "__file__", None),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {
            "name": name,
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def resolve_entrypoint(entrypoint: str, module: str) -> tuple[list[str], str]:
    command = shutil.which(entrypoint)
    if command:
        return [command, "--help"], "entrypoint"
    sibling = Path(sys.executable).with_name(entrypoint)
    if sibling.exists():
        return [str(sibling), "--help"], "python-bin-sibling"
    return [sys.executable, "-m", module, "--help"], "python-module-fallback"


def check_cli(entrypoint: str, module: str) -> dict[str, Any]:
    command, source = resolve_entrypoint(entrypoint, module)
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {
            "name": entrypoint,
            "module": module,
            "ok": False,
            "source": source,
            "command": command,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "name": entrypoint,
        "module": module,
        "ok": proc.returncode == 0,
        "source": source,
        "command": command,
        "returncode": proc.returncode,
        "stdout_preview": preview(proc.stdout),
        "stderr_preview": preview(proc.stderr),
    }


def make_report(skip_cli: bool) -> dict[str, Any]:
    imports = [check_import(name) for name in IMPORT_TARGETS]
    clis = [] if skip_cli else [check_cli(name, module) for name, module in CLI_TARGETS]
    ok = all(item["ok"] for item in imports) and all(item["ok"] for item in clis)
    return {
        "ok": ok,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "sana_distribution_version": package_version("sana"),
        "environment_defaults": {
            "DISABLE_XFORMERS": os.environ.get("DISABLE_XFORMERS"),
            "DISABLE_FLASH_ATTN": os.environ.get("DISABLE_FLASH_ATTN"),
        },
        "imports": imports,
        "cli": clis,
    }


def print_text(report: dict[str, Any]) -> None:
    print("# Sana install smoke check")
    print(f"Python: {report['python']}")
    print(f"Sana distribution version: {report['sana_distribution_version'] or 'not installed'}")
    print("\n## Imports")
    for item in report["imports"]:
        status = "PASS" if item["ok"] else "FAIL"
        detail = item.get("module_file") or item.get("error", "")
        print(f"- {status}: {item['name']} {detail}")
    if report["cli"]:
        print("\n## CLI --help")
        for item in report["cli"]:
            status = "PASS" if item["ok"] else "FAIL"
            print(f"- {status}: {item['name']} via {item['source']} rc={item.get('returncode')}")
            if not item["ok"] and item.get("stderr_preview"):
                print(f"  stderr: {' | '.join(item['stderr_preview'])}")
    print(f"\nOverall: {'PASS' if report['ok'] else 'FAIL'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-cli", action="store_true", help="Do not run sana-run/sana-upload --help checks.")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    args = parser.parse_args()

    report = make_report(skip_cli=args.skip_cli)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

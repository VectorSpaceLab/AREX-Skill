#!/usr/bin/env python3
"""Inspect a Semantra installation without downloading models or starting a server.

Examples:
  python inspect_semantra_install.py
  python inspect_semantra_install.py --json
  python inspect_semantra_install.py --semantra-command semantra
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any


def run_cmd(args: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
        return {
            "command": args,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"command": args, "returncode": None, "error": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": args,
            "returncode": None,
            "error": f"timed out after {timeout}s",
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
        }


def inspect_imports() -> dict[str, Any]:
    result: dict[str, Any] = {"imports": {}, "distribution": {}}
    try:
        result["distribution"] = {
            "name": "semantra",
            "version": metadata.version("semantra"),
            "requires": metadata.requires("semantra") or [],
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["distribution"] = {"error": repr(exc)}

    for module_name in [
        "semantra",
        "semantra.semantra",
        "semantra.models",
        "semantra.pdf",
        "semantra.util",
    ]:
        try:
            module = importlib.import_module(module_name)
            result["imports"][module_name] = {
                "ok": True,
                "file_basename": getattr(module, "__file__", None).split("/")[-1]
                if getattr(module, "__file__", None)
                else None,
            }
        except Exception as exc:  # pragma: no cover - diagnostic path
            result["imports"][module_name] = {"ok": False, "error": repr(exc)}
    return result


def inspect_registry() -> dict[str, Any]:
    try:
        from semantra import models as semantra_models
        from semantra import semantra as semantra_cli
        from semantra import util as semantra_util

        return {
            "version_constant": getattr(semantra_cli, "VERSION", None),
            "default_encoding": getattr(semantra_cli, "DEFAULT_ENCODING", None),
            "default_port": getattr(semantra_cli, "DEFAULT_PORT", None),
            "hash_length": getattr(semantra_util, "HASH_LENGTH", None),
            "preset_models": {
                name: {k: v for k, v in config.items() if k != "get_model"}
                for name, config in semantra_models.models.items()
            },
            "process_windows_sample": list(
                semantra_cli.process_windows("128_0_16,64_8")
            ),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"error": repr(exc)}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    command = args.semantra_command or shutil.which("semantra") or "semantra"
    report = {
        "python": sys.version.split()[0],
        "imports": inspect_imports(),
        "registry": inspect_registry(),
        "cli": {},
    }
    if args.skip_cli:
        report["cli"] = {"skipped": True}
    else:
        report["cli"] = {
            "version": run_cmd([command, "--version"], timeout=args.timeout),
            "list_models": run_cmd([command, "--list-models"], timeout=args.timeout),
            "help": run_cmd([command, "--help"], timeout=args.timeout),
        }
    return report


def print_text(report: dict[str, Any]) -> None:
    dist = report["imports"].get("distribution", {})
    print(f"Semantra distribution: {dist.get('version', 'unknown')}")
    print(f"Python: {report['python']}")
    print("\nImports:")
    for module, info in report["imports"].get("imports", {}).items():
        status = "ok" if info.get("ok") else f"FAILED: {info.get('error')}"
        print(f"  - {module}: {status}")
    print("\nPreset models:")
    presets = report.get("registry", {}).get("preset_models", {})
    for name, config in presets.items():
        print(f"  - {name}: {config}")
    if report.get("registry", {}).get("error"):
        print(f"Registry error: {report['registry']['error']}")
    print("\nCLI checks:")
    for name, check in report.get("cli", {}).items():
        if name == "skipped":
            print("  - skipped")
            continue
        print(f"  - {name}: returncode={check.get('returncode')} error={check.get('error', '')}")
        stdout = check.get("stdout") or ""
        if stdout:
            print("    " + stdout.splitlines()[0][:160])
        stderr = check.get("stderr") or ""
        if stderr:
            print("    stderr: " + stderr.splitlines()[0][:160])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit the full report as JSON.")
    parser.add_argument(
        "--semantra-command",
        default=None,
        help="Semantra CLI command or path to run for safe --help/--version checks.",
    )
    parser.add_argument("--skip-cli", action="store_true", help="Only inspect Python imports.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout for each CLI check.")
    args = parser.parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    imports = report.get("imports", {}).get("imports", {})
    failed = [name for name, info in imports.items() if not info.get("ok")]
    cli_failures = [
        name
        for name, info in report.get("cli", {}).items()
        if isinstance(info, dict) and info.get("returncode") not in (0, None)
    ]
    return 1 if failed or cli_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

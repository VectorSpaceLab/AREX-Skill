#!/usr/bin/env python3
"""Non-mutating diagnostics for Dagster component project tooling."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
from importlib import metadata
from typing import Any


def probe_import(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - environment-dependent
        return {"name": module_name, "ok": False, "detail": repr(exc)}

    version = getattr(module, "__version__", None)
    if version is None:
        package_name = module_name.split(".")[0].replace("_", "-")
        try:
            version = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            version = "imported; package metadata not found"
    return {"name": module_name, "ok": True, "detail": str(version)}


def probe_command(command_name: str) -> dict[str, Any]:
    executable = shutil.which(command_name)
    if executable is None:
        return {
            "name": command_name,
            "ok": False,
            "executable": None,
            "help_ok": False,
            "detail": "not found on PATH",
        }

    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover - environment-dependent
        return {
            "name": command_name,
            "ok": False,
            "executable": executable,
            "help_ok": False,
            "detail": repr(exc),
        }

    help_ok = completed.returncode == 0
    first_line = (completed.stdout or completed.stderr).strip().splitlines()
    detail = first_line[0] if first_line else f"exit code {completed.returncode}"
    return {
        "name": command_name,
        "ok": help_ok,
        "executable": executable,
        "help_ok": help_ok,
        "detail": detail,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether Dagster component APIs and project CLI entry points are "
            "available without installing packages, creating files, or starting services."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--require-dg",
        action="store_true",
        help="Exit nonzero when the dg command is unavailable or its --help fails.",
    )
    parser.add_argument(
        "--require-create-dagster",
        action="store_true",
        help="Exit nonzero when create-dagster is unavailable or its --help fails.",
    )
    return parser


def report_text(imports: list[dict[str, Any]], commands: list[dict[str, Any]]) -> str:
    lines = ["Dagster component project doctor", "", "Imports:"]
    for probe in imports:
        status = "ok" if probe["ok"] else "missing"
        lines.append(f"- {probe['name']}: {status} ({probe['detail']})")

    lines.extend(["", "Commands:"])
    for probe in commands:
        status = "ok" if probe["ok"] else "missing"
        executable = probe["executable"] or "not found"
        lines.append(f"- {probe['name']}: {status} ({executable}; {probe['detail']})")

    lines.extend(
        [
            "",
            "Guidance:",
            "- dagster.components must import before component APIs can be used.",
            "- Missing dg/create-dagster usually means project CLI tooling is not installed or not on PATH.",
            "- This script does not install packages, create projects, or start Dagster services.",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    import_probes = [
        probe_import("dagster"),
        probe_import("dagster.components"),
        probe_import("dagster_dg_cli"),
        probe_import("dagster_dg_core"),
        probe_import("create_dagster"),
    ]
    command_probes = [probe_command("dg"), probe_command("create-dagster")]

    payload: dict[str, Any] = {
        "imports": import_probes,
        "commands": command_probes,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(report_text(import_probes, command_probes))

    command_status = {str(probe["name"]): bool(probe["ok"]) for probe in command_probes}
    if args.require_dg and not command_status["dg"]:
        return 2
    if args.require_create_dagster and not command_status["create-dagster"]:
        return 3
    if not import_probes[1]["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

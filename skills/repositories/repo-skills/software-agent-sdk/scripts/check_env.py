#!/usr/bin/env python3
"""Check an OpenHands Software Agent SDK runtime environment.

This helper is intentionally safe: it imports packages, prints distribution
versions, inspects the tool registry, and optionally checks agent-server help.
It does not require LLM credentials and does not start a long-running server.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any


os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")


DISTRIBUTIONS = [
    "openhands-sdk",
    "openhands-tools",
    "openhands-workspace",
    "openhands-agent-server",
]
IMPORTS = [
    "openhands.sdk",
    "openhands.tools",
    "openhands.workspace",
    "openhands.agent_server",
]
OPTIONAL_TOOL_MODULES = [
    "openhands.tools.apply_patch.definition",
    "openhands.tools.browser_use.definition",
    "openhands.tools.delegate.definition",
    "openhands.tools.file_editor.definition",
    "openhands.tools.glob.definition",
    "openhands.tools.grep.definition",
    "openhands.tools.planning_file_editor.definition",
    "openhands.tools.task.definition",
    "openhands.tools.task_tracker.definition",
    "openhands.tools.terminal.definition",
    "openhands.tools.tom_consult.definition",
    "openhands.tools.workflow.definition",
]


def _version(dist: str) -> str | None:
    try:
        return version(dist)
    except PackageNotFoundError:
        return None


def _import(name: str) -> dict[str, Any]:
    try:
        importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True}


def _tool_report(load_all_tools: bool) -> dict[str, Any]:
    if load_all_tools:
        for module in OPTIONAL_TOOL_MODULES:
            try:
                importlib.import_module(module)
            except Exception as exc:  # noqa: BLE001 - optional diagnostics
                print(
                    f"warning: failed to import optional tool module {module}: {exc}",
                    file=sys.stderr,
                )
    try:
        from openhands.sdk.tool.registry import (
            get_tool_module_qualnames,
            list_registered_tools,
            list_usable_tools,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "registered": list_registered_tools(),
        "usable": list_usable_tools(),
        "module_qualnames": get_tool_module_qualnames(),
    }


def _agent_server_help() -> dict[str, Any]:
    env = os.environ.copy()
    env.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")
    proc = subprocess.run(
        [sys.executable, "-m", "openhands.agent_server", "--help"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
        timeout=30,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_head": proc.stdout[:2000],
        "stderr_head": proc.stderr[:2000],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "python": sys.version,
        "executable": sys.executable,
        "distributions": {dist: _version(dist) for dist in DISTRIBUTIONS},
        "imports": [_import(name) for name in IMPORTS],
        "tools": _tool_report(args.load_all_tools),
        "agent_server_help": _agent_server_help() if args.agent_server_help else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--load-all-tools",
        action="store_true",
        help="Import all known built-in tool modules before listing the registry.",
    )
    parser.add_argument(
        "--agent-server-help",
        action="store_true",
        help="Run `python -m openhands.agent_server --help` as a smoke check.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    imports_ok = all(item["ok"] for item in report["imports"])
    tools_ok = bool(report["tools"].get("ok"))
    help_report = report.get("agent_server_help")
    help_ok = True if help_report is None else bool(help_report.get("ok"))
    return 0 if imports_ok and tools_ok and help_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

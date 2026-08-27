#!/usr/bin/env python3
"""List and lightly probe installed Dipy CLI workflows.

This helper is self-contained and network-free. It reads
``dipy.workflows.cli.cli_flows`` from the active Python environment, groups flows
by workflow module, and can run bounded ``--help`` checks for selected console
entry points. It does not execute data-processing workflows.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from importlib import metadata
from typing import Any


def _head(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...<truncated>"


def _load_cli_flows() -> tuple[dict[str, tuple[str, str]], dict[str, Any]]:
    facts: dict[str, Any] = {
        "import_ok": False,
        "dipy_version": None,
        "distribution_version": None,
        "error": None,
    }
    try:
        import dipy
        from dipy.workflows.cli import cli_flows

        facts["import_ok"] = True
        facts["dipy_version"] = getattr(dipy, "__version__", None)
        try:
            facts["distribution_version"] = metadata.version("dipy")
        except metadata.PackageNotFoundError:
            facts["distribution_version"] = None

        normalized: dict[str, tuple[str, str]] = {}
        for command, target in cli_flows.items():
            if isinstance(target, tuple) and len(target) == 2:
                module_name, class_name = target
            else:
                module_name = getattr(target, "__module__", "")
                class_name = getattr(target, "__name__", repr(target))
            normalized[command] = (str(module_name), str(class_name))
        return normalized, facts
    except Exception as exc:  # pragma: no cover - diagnostic path
        facts["error"] = f"{type(exc).__name__}: {exc}"
        return {}, facts


def _group_flows(flows: dict[str, tuple[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for command, (module_name, class_name) in sorted(flows.items()):
        family = module_name.rsplit(".", 1)[-1] if module_name else "unknown"
        groups[family].append(
            {"command": command, "module": module_name, "class": class_name}
        )
    return dict(sorted(groups.items()))


def _optional_dependency_status() -> dict[str, str]:
    modules = ["fury", "matplotlib", "torch", "tensorflow"]
    status: dict[str, str] = {}
    for module_name in modules:
        spec = importlib.util.find_spec(module_name)
        status[module_name] = "available" if spec is not None else "not_found"
    return status


def _check_help(command: str, timeout: float) -> dict[str, Any]:
    executable = shutil.which(command)
    result: dict[str, Any] = {
        "command": command,
        "executable_found": executable is not None,
        "returncode": None,
        "timed_out": False,
        "stdout_head": "",
        "stderr_head": "",
        "error": None,
    }
    if executable is None:
        result["error"] = "entry point not found on PATH"
        return result

    try:
        completed = subprocess.run(
            [executable, "--help"],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        result["timed_out"] = True
        result["stdout_head"] = _head(exc.stdout or "")
        result["stderr_head"] = _head(exc.stderr or "")
        result["error"] = f"help probe timed out after {timeout:g}s"
        return result
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["returncode"] = completed.returncode
    result["stdout_head"] = _head(completed.stdout)
    result["stderr_head"] = _head(completed.stderr)
    return result


def _render_text(payload: dict[str, Any]) -> str:
    lines = []
    facts = payload["facts"]
    lines.append("Dipy CLI probe")
    lines.append(f"import_ok: {facts['import_ok']}")
    lines.append(f"dipy_version: {facts['dipy_version']}")
    lines.append(f"distribution_version: {facts['distribution_version']}")
    if facts.get("error"):
        lines.append(f"error: {facts['error']}")
    lines.append(f"flow_count: {payload['flow_count']}")
    lines.append("")
    for family, entries in payload["families"].items():
        lines.append(f"[{family}] {len(entries)}")
        for entry in entries:
            lines.append(
                f"  {entry['command']} -> {entry['module']}:{entry['class']}"
            )
    lines.append("")
    lines.append("optional_dependencies:")
    for name, status in payload["optional_dependencies"].items():
        lines.append(f"  {name}: {status}")
    if payload.get("help_checks"):
        lines.append("")
        lines.append("help_checks:")
        for check in payload["help_checks"]:
            lines.append(
                "  {command}: found={found} returncode={code} timed_out={timed}".format(
                    command=check["command"],
                    found=check["executable_found"],
                    code=check["returncode"],
                    timed=check["timed_out"],
                )
            )
            if check.get("error"):
                lines.append(f"    error: {check['error']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List installed Dipy CLI workflows and optionally probe --help."
    )
    parser.add_argument(
        "--check-help",
        nargs="*",
        default=[],
        metavar="COMMAND",
        help="Selected dipy_* entry points to run with --help under a timeout.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=8.0,
        help="Seconds allowed for each --help probe. Default: 8.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. Default: json.",
    )
    args = parser.parse_args(argv)

    flows, facts = _load_cli_flows()
    payload: dict[str, Any] = {
        "facts": facts,
        "flow_count": len(flows),
        "families": _group_flows(flows),
        "optional_dependencies": _optional_dependency_status(),
        "help_checks": [_check_help(command, args.timeout) for command in args.check_help],
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_text(payload), end="")
    return 0 if facts["import_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check that an environment can use core MTEB APIs without running benchmarks."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import json
import shutil
import subprocess
import sys
from typing import Any


def _run_help(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    return {
        "command": command,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_first_line": completed.stdout.splitlines()[0] if completed.stdout.splitlines() else "",
        "stderr_first_line": completed.stderr.splitlines()[0] if completed.stderr.splitlines() else "",
    }


def _command_help(args: list[str]) -> dict[str, Any]:
    commands: list[list[str]] = []
    if shutil.which("mteb") is not None:
        commands.append(["mteb", *args])
    commands.append([sys.executable, "-m", "mteb", *args])

    attempts = [_run_help(command) for command in commands]
    for attempt in attempts:
        if attempt["ok"]:
            result = dict(attempt)
            result["attempts"] = attempts
            return result
    return {
        "command": commands[0] if commands else ["mteb", *args],
        "ok": False,
        "error": "no CLI help form succeeded",
        "attempts": attempts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--skip-cli",
        action="store_true",
        help="Skip mteb command-line help checks.",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {"ok": False, "checks": {}}

    try:
        import mteb
    except Exception as exc:  # pragma: no cover - diagnostic script
        report["checks"]["import"] = {"ok": False, "error": repr(exc)}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"MTEB import failed: {exc}", file=sys.stderr)
        return 1

    report["checks"]["import"] = {"ok": True, "version": getattr(mteb, "__version__", None)}

    try:
        report["checks"]["distribution"] = {
            "ok": True,
            "version": metadata.version("mteb"),
        }
    except metadata.PackageNotFoundError as exc:
        report["checks"]["distribution"] = {"ok": False, "error": repr(exc)}

    api_checks = {
        "evaluate": mteb.evaluate,
        "get_tasks": mteb.get_tasks,
        "get_task": mteb.get_task,
        "get_benchmark": mteb.get_benchmark,
        "get_model": mteb.get_model,
        "load_results": mteb.load_results,
    }
    report["checks"]["signatures"] = {
        name: str(inspect.signature(obj)) for name, obj in api_checks.items()
    }

    try:
        tasks = mteb.get_tasks(tasks=["Banking77Classification.v2"])
        report["checks"]["task_lookup"] = {
            "ok": len(tasks) == 1,
            "count": len(tasks),
            "names": [task.metadata.name for task in tasks],
        }
    except Exception as exc:
        report["checks"]["task_lookup"] = {"ok": False, "error": repr(exc)}

    if not args.skip_cli:
        report["checks"]["cli"] = {
            "mteb": _command_help(["--help"]),
            "run": _command_help(["run", "--help"]),
            "available_tasks": _command_help(["available-tasks", "--help"]),
            "available_benchmarks": _command_help(["available-benchmarks", "--help"]),
            "create_model_results": _command_help(["create-model-results", "--help"]),
        }

    report["ok"] = bool(
        report["checks"]["import"]["ok"]
        and report["checks"].get("distribution", {}).get("ok", False)
        and report["checks"].get("task_lookup", {}).get("ok", False)
        and (
            args.skip_cli
            or all(value.get("ok") for value in report["checks"].get("cli", {}).values())
        )
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"MTEB import: {report['checks']['import']}")
        print(f"Distribution: {report['checks']['distribution']}")
        print(f"Task lookup: {report['checks']['task_lookup']}")
        if not args.skip_cli:
            for name, result in report["checks"]["cli"].items():
                print(f"CLI {name}: {result}")
        print(f"Overall ok: {report['ok']}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

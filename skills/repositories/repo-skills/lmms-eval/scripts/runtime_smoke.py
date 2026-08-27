#!/usr/bin/env python3
"""Quick package and CLI smoke for lmms-eval.

This helper stays within the generated skill tree and avoids any dependence on
an original repository checkout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Iterable


def run_cli(args: Iterable[str]) -> dict:
    proc = subprocess.run(["lmms-eval", *args], capture_output=True, text=True)
    return {
        "args": list(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout[:2000],
        "stderr": proc.stderr[:2000],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small lmms-eval package smoke check.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    report: dict = {"package": {}, "imports": [], "registry": {}, "cli": []}

    try:
        report["package"]["distribution_version"] = version("lmms-eval")
    except PackageNotFoundError:
        report["package"]["distribution_version"] = "not-installed"

    import lmms_eval
    from lmms_eval.entrypoints import ServerArgs
    from lmms_eval.models import list_available_models
    from lmms_eval.tasks import TaskManager

    report["package"]["module_path"] = str(Path(lmms_eval.__file__).resolve())
    report["imports"].extend(
        [
            "lmms_eval",
            "lmms_eval.entrypoints",
            "lmms_eval.models",
            "lmms_eval.tasks",
        ]
    )

    task_manager = TaskManager("ERROR")
    report["registry"]["subtasks"] = len(task_manager.all_subtasks)
    report["registry"]["groups"] = len(task_manager.all_groups)
    report["registry"]["tags"] = len(task_manager.all_tags)
    report["registry"]["models"] = len(list_available_models())
    report["registry"]["server_args"] = ServerArgs().to_dict()

    for cli_args in (
        ["--help"],
        ["version"],
        ["tasks", "--help"],
        ["models", "--aliases"],
        ["serve", "--help"],
        ["mcp", "--help"],
        ["ui", "--help"],
        ["tui", "--help"],
    ):
        report["cli"].append(run_cli(cli_args))

    failures = [entry for entry in report["cli"] if entry["returncode"] != 0]
    if failures:
        report["status"] = "failed"
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    report["status"] = "ok"
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"lmms-eval {report['package']['distribution_version']}")
        print(f"imports: {', '.join(report['imports'])}")
        print(
            "registry: "
            f"{report['registry']['subtasks']} subtasks, "
            f"{report['registry']['groups']} groups, "
            f"{report['registry']['tags']} tags, "
            f"{report['registry']['models']} models"
        )
        print("cli: all smoke commands returned 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

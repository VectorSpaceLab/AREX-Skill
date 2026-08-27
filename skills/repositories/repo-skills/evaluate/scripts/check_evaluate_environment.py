#!/usr/bin/env python3
"""Safely inspect a Hugging Face Evaluate installation without downloads or Hub mutation.

Example:
  python check_evaluate_environment.py --json
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


def distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def run_cli_help() -> dict[str, Any]:
    executable = shutil.which("evaluate-cli")
    if not executable:
        return {"available": False, "ok": False, "reason": "evaluate-cli not on PATH"}
    try:
        proc = subprocess.run(
            [executable, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        return {"available": True, "ok": False, "reason": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_head": proc.stdout.splitlines()[:8],
        "stderr_head": proc.stderr.splitlines()[:8],
    }


def inspect_environment() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {
            name: distribution_version(name)
            for name in [
                "evaluate",
                "datasets",
                "huggingface-hub",
                "transformers",
                "scipy",
                "cookiecutter",
                "gradio",
                "matplotlib",
                "torch",
                "tensorflow",
                "flax",
            ]
        },
        "optional_imports": {},
        "evaluate": {"import_ok": False},
        "cli": {},
    }

    for module_name in ["datasets", "transformers", "scipy", "cookiecutter", "gradio", "matplotlib", "torch", "tensorflow", "flax"]:
        report["optional_imports"][module_name] = has_module(module_name)

    try:
        import evaluate

        report["evaluate"] = {
            "import_ok": True,
            "version": getattr(evaluate, "__version__", None),
            "has_load": hasattr(evaluate, "load"),
            "has_combine": hasattr(evaluate, "combine"),
            "has_evaluator": hasattr(evaluate, "evaluator"),
        }
        try:
            from evaluate.evaluator import get_supported_tasks

            report["evaluate"]["supported_evaluator_tasks"] = get_supported_tasks()
        except Exception as exc:
            report["evaluate"]["supported_evaluator_tasks_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        report["evaluate"] = {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}

    report["cli"] = run_cli_help()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    report = inspect_environment()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Evaluate import: {report['evaluate'].get('import_ok')} version={report['evaluate'].get('version')}")
        print(f"CLI help: {report['cli'].get('ok')} ({report['cli'].get('reason', report['cli'].get('returncode'))})")
        missing = [name for name, ok in report["optional_imports"].items() if not ok]
        print("Missing optional imports: " + (", ".join(missing) if missing else "none"))
    return 0 if report["evaluate"].get("import_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

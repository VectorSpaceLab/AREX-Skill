#!/usr/bin/env python3
"""Check lm-evaluation-harness CLI and import surfaces safely.

This helper runs help commands and lightweight imports only. It does not run
model inference, download datasets, or instantiate model backends.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_help(executable: str, args: list[str], timeout: float) -> CheckResult:
    label = " ".join([executable, *args])
    path = shutil.which(executable)
    if path is None:
        return CheckResult(label, False, "executable not found on PATH")
    try:
        completed = subprocess.run(
            [path, *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(label, False, f"timed out after {timeout:g}s")
    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        return CheckResult(label, False, f"exit {completed.returncode}: {output[:500].strip()}")
    expected = []
    if args == ["--help"]:
        expected = ["run", "ls", "validate"]
    elif args == ["run", "--help"]:
        expected = ["--config", "--tasks", "--model", "--model_args", "--output_path"]
    elif args == ["ls", "--help"]:
        expected = ["tasks", "groups", "subtasks", "tags"]
    elif args == ["validate", "--help"]:
        expected = ["--tasks", "--include_path"]
    missing = [token for token in expected if token not in output]
    if missing:
        return CheckResult(label, False, f"help missing expected tokens: {', '.join(missing)}")
    return CheckResult(label, True, "help ok")


def check_imports() -> list[CheckResult]:
    checks: list[CheckResult] = []
    for module_name in ["lm_eval", "lm_eval.evaluator", "lm_eval.config.evaluate_config"]:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            checks.append(CheckResult(f"import {module_name}", False, repr(exc)))
            continue
        checks.append(CheckResult(f"import {module_name}", True, getattr(module, "__name__", module_name)))
    try:
        from lm_eval.config.evaluate_config import EvaluatorConfig
        from lm_eval.evaluator import simple_evaluate
    except Exception as exc:  # noqa: BLE001
        checks.append(CheckResult("public api objects", False, repr(exc)))
    else:
        detail = f"EvaluatorConfig={EvaluatorConfig.__name__}, simple_evaluate={simple_evaluate.__name__}"
        checks.append(CheckResult("public api objects", True, detail))
    return checks


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=15.0, help="Seconds per help command")
    parser.add_argument("--skip-help", action="store_true", help="Only check Python imports")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    results = check_imports()
    if not args.skip_help:
        for executable in ["lm-eval", "lm_eval"]:
            for help_args in [["--help"], ["run", "--help"], ["ls", "--help"], ["validate", "--help"]]:
                results.append(run_help(executable, help_args, args.timeout))
    ok = all(result.ok for result in results)
    if args.json:
        print(json.dumps({"ok": ok, "checks": [asdict(result) for result in results]}, indent=2))
    else:
        for result in results:
            status = "ok" if result.ok else "FAIL"
            print(f"[{status}] {result.name}: {result.detail}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

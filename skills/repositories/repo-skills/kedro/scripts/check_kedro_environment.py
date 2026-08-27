#!/usr/bin/env python3
"""Safe Kedro environment diagnostics for agents.

This helper checks importability, distribution metadata, optional modules, and
CLI availability without requiring a Kedro project checkout.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str


def _print(result: CheckResult) -> None:
    print(f"{result.status}: {result.name} - {result.detail}")


def _dist_check() -> CheckResult:
    try:
        version = metadata.version("kedro")
    except metadata.PackageNotFoundError:
        return CheckResult("distribution", "FAIL", "Python distribution 'kedro' is not installed")
    return CheckResult("distribution", "PASS", f"kedro {version}")


def _import_check(module: str) -> CheckResult:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report any import failure
        return CheckResult(f"import {module}", "FAIL", f"{type(exc).__name__}: {exc}")
    version = getattr(imported, "__version__", None)
    suffix = f" version {version}" if version else ""
    return CheckResult(f"import {module}", "PASS", f"module imports{suffix}")


def _optional_check(module: str, install_hint: str) -> CheckResult:
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001
        return CheckResult(f"optional {module}", "WARN", f"not importable ({type(exc).__name__}); install {install_hint} if this workflow needs it")
    return CheckResult(f"optional {module}", "PASS", "module imports")


def _run_cli(args: list[str], timeout: int) -> CheckResult:
    executable = shutil.which("kedro")
    if not executable:
        return CheckResult("kedro CLI", "WARN", "'kedro' is not on PATH; try 'python -m kedro --help' from the intended environment")

    env = os.environ.copy()
    env.setdefault("KEDRO_DISABLE_TELEMETRY", "1")
    env.setdefault("DO_NOT_TRACK", "1")
    command = [executable, *args]
    try:
        completed = subprocess.run(
            command,
            check=False,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult("kedro CLI", "FAIL", f"command timed out: {' '.join(command)}")

    output = (completed.stdout or completed.stderr).strip().splitlines()
    first_line = output[0] if output else "no output"
    if completed.returncode != 0:
        return CheckResult("kedro CLI", "FAIL", f"exit {completed.returncode}: {first_line}")
    return CheckResult("kedro CLI", "PASS", first_line)


def _project_probe(path: str) -> CheckResult:
    try:
        from kedro.utils import find_kedro_project, is_kedro_project
    except Exception as exc:  # noqa: BLE001
        return CheckResult("project probe", "FAIL", f"cannot import Kedro project helpers: {type(exc).__name__}: {exc}")

    candidate = os.path.abspath(path)
    found = find_kedro_project(candidate)
    if found:
        return CheckResult("project probe", "PASS", f"found Kedro project at or above {path!r}")
    direct = is_kedro_project(candidate)
    if direct:
        return CheckResult("project probe", "PASS", f"{path!r} is a Kedro project")
    return CheckResult("project probe", "WARN", f"no Kedro project detected at or above {path!r}")


def run_checks(args: argparse.Namespace) -> int:
    results: list[CheckResult] = [_dist_check(), _import_check("kedro")]

    if args.check_optional:
        results.extend(
            [
                _optional_check("kedro_datasets", "kedro-datasets and dataset-specific extras"),
                _optional_check("IPython", "kedro[jupyter] or notebook dependencies"),
                _optional_check("fastapi", "kedro[server] for server workflows"),
                _optional_check("uvicorn", "kedro[server] for server workflows"),
            ]
        )

    if args.check_cli:
        results.append(_run_cli(["--version"], args.timeout))
        results.append(_run_cli(["--help"], args.timeout))

    if args.project_path:
        results.append(_project_probe(args.project_path))

    for result in results:
        _print(result)

    return 1 if any(result.status == "FAIL" for result in results) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run safe Kedro import, metadata, optional dependency, CLI, and project-detection diagnostics.")
    parser.add_argument("--check-cli", action="store_true", help="Run telemetry-disabled 'kedro --version' and 'kedro --help' if the console script is on PATH.")
    parser.add_argument("--check-optional", action="store_true", help="Check optional modules used by datasets, notebooks, and server workflows.")
    parser.add_argument("--project-path", help="Read-only probe for Kedro project detection at or above this path.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds for each CLI command. Default: 20.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    return run_checks(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())

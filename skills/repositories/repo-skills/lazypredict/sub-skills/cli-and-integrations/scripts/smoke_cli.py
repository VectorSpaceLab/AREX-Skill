#!/usr/bin/env python3
"""Smoke-test the Lazy Predict CLI command object with tiny temporary CSVs.

Examples:
    python scripts/smoke_cli.py --task classification
    python scripts/smoke_cli.py --task both --skip-fit

By default this uses Click's in-process CliRunner so it works even when the
console script is not on PATH. If the installed `lazypredict` executable exists,
it also checks `lazypredict --version`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
from click.testing import CliRunner
from sklearn.datasets import load_breast_cancer, load_diabetes

from lazypredict import cli


def make_csv(task: str, directory: Path) -> tuple[Path, str]:
    if task == "classification":
        data = load_breast_cancer()
        df = pd.DataFrame(data.data[:60, :5], columns=[f"f{i}" for i in range(5)])
        df["target"] = data.target[:60]
    else:
        data = load_diabetes()
        df = pd.DataFrame(data.data[:80, :5], columns=[f"f{i}" for i in range(5)])
        df["target"] = data.target[:80]
    path = directory / f"lazypredict_{task}.csv"
    df.to_csv(path, index=False)
    return path, "target"


def run_command_object(task: str, skip_fit: bool) -> dict:
    runner = CliRunner()
    if skip_fit:
        result = runner.invoke(cli.main, ["--help"])
        return {"task": task, "mode": "help", "exit_code": result.exit_code, "ok": result.exit_code == 0}
    with runner.isolated_filesystem():
        cwd = Path.cwd()
        csv_path, target = make_csv(task, cwd)
        result = runner.invoke(
            cli.main,
            ["--task", task, "--input", str(csv_path), "--target", target, "--test-size", "0.25", "--random-state", "7"],
            catch_exceptions=False,
        )
        expected = "Accuracy" if task == "classification" else "R-Squared"
        ok = result.exit_code == 0 and expected in result.output
        return {
            "task": task,
            "mode": "fit",
            "exit_code": result.exit_code,
            "ok": ok,
            "expected_text": expected,
            "output_head": result.output.splitlines()[:5],
        }


def console_version() -> dict:
    exe = shutil.which("lazypredict")
    if not exe:
        return {"available_on_path": False}
    proc = subprocess.run([exe, "--version"], text=True, capture_output=True, timeout=30)
    return {
        "available_on_path": True,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test Lazy Predict CLI behavior.")
    parser.add_argument("--task", choices=["classification", "regression", "both"], default="classification")
    parser.add_argument("--skip-fit", action="store_true", help="Only check help/version paths, not CSV fitting.")
    args = parser.parse_args(argv)

    tasks = ["classification", "regression"] if args.task == "both" else [args.task]
    runs = [run_command_object(task, args.skip_fit) for task in tasks]
    report = {"ok": all(item["ok"] for item in runs), "runs": runs, "console_version": console_version()}
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - smoke failure path
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2), file=sys.stderr)
        raise

#!/usr/bin/env python3
"""Smoke-test Optuna's installed CLI with temporary SQLite storage."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SEARCH_SPACE = json.dumps(
    {
        "x": {
            "name": "FloatDistribution",
            "attributes": {"low": -10.0, "high": 10.0, "step": None, "log": False},
        }
    }
)


def run(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def optuna_command() -> list[str]:
    optuna_cmd = shutil.which("optuna")
    if optuna_cmd is not None:
        return [optuna_cmd]

    try:
        import optuna.cli  # noqa: F401
    except ModuleNotFoundError:
        print("neither the optuna console script nor importable optuna.cli was found", file=sys.stderr)
        raise SystemExit(2)

    return [sys.executable, "-c", "import optuna.cli; raise SystemExit(optuna.cli.main())"]


def main() -> int:
    optuna_cmd = optuna_command()

    with tempfile.TemporaryDirectory(prefix="optuna-cli-smoke-") as temp_dir:
        db_path = Path(temp_dir) / "study.db"
        storage = f"sqlite:///{db_path}"
        study_name = "cli-smoke"

        created = run(
            [
                *optuna_cmd,
                "create-study",
                "--storage",
                storage,
                "--study-name",
                study_name,
                "--direction",
                "minimize",
                "--skip-if-exists",
            ]
        )
        if created != study_name:
            raise AssertionError(f"expected study name {study_name!r}, got {created!r}")

        ask_output = run(
            [
                *optuna_cmd,
                "ask",
                "--storage",
                storage,
                "--study-name",
                study_name,
                "--sampler",
                "TPESampler",
                "--sampler-kwargs",
                '{"seed": 0}',
                "--search-space",
                SEARCH_SPACE,
                "--format",
                "json",
            ]
        )
        asked = json.loads(ask_output)
        trial_number = asked["number"]
        if not isinstance(trial_number, int):
            raise AssertionError(f"trial number should be int, got {trial_number!r}")
        if "x" not in asked.get("params", {}):
            raise AssertionError(f"ask output missing suggested x parameter: {asked!r}")

        objective_value = (float(asked["params"]["x"]) - 2.0) ** 2
        run(
            [
                *optuna_cmd,
                "tell",
                "--storage",
                storage,
                "--study-name",
                study_name,
                "--trial-number",
                str(trial_number),
                "--values",
                str(objective_value),
                "--state",
                "complete",
            ]
        )

        trials_output = run(
            [
                *optuna_cmd,
                "trials",
                "--storage",
                storage,
                "--study-name",
                study_name,
                "--format",
                "json",
                "--flatten",
            ]
        )
        trials = json.loads(trials_output)
        if len(trials) != 1:
            raise AssertionError(f"expected one trial, got {len(trials)}: {trials!r}")
        trial = trials[0]
        if trial.get("state") != "COMPLETE":
            raise AssertionError(f"expected COMPLETE trial, got {trial!r}")
        if "params_x" not in trial:
            raise AssertionError(f"flattened trial output missing params_x: {trial!r}")

    print("Optuna CLI SQLite ask/tell smoke succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

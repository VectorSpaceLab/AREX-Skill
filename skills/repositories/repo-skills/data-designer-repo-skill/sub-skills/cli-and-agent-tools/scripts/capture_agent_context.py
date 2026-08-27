#!/usr/bin/env python3
"""Capture a safe Data Designer CLI and agent-introspection snapshot.

The script wraps the installed CLI. It does not import source checkout modules or
assume repository paths. By default it runs the CLI with a temporary
DATA_DESIGNER_HOME so normal user config files are not mutated by the CLI's
startup bootstrap. Pass --home to capture a specific Data Designer state
location.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

CAPTURE_COMMANDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("root_help", ("--help",)),
    ("config_help", ("config", "--help")),
    ("download_help", ("download", "--help")),
    ("plugin_help", ("plugin", "--help")),
    ("agent_help", ("agent", "--help")),
    ("agent_context", ("agent", "context")),
    ("agent_types", ("agent", "types")),
    ("agent_model_aliases", ("agent", "state", "model-aliases")),
    ("agent_persona_datasets", ("agent", "state", "persona-datasets")),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture root/group help plus `data-designer agent` context/state outputs "
            "from an installed Data Designer CLI."
        )
    )
    parser.add_argument(
        "--cli",
        nargs="+",
        help=(
            "Command prefix to run. Defaults to `data-designer` when it is on PATH, "
            "otherwise `python -m data_designer.cli.main` with the current Python. "
            "Examples: --cli data-designer ; --cli python -m data_designer.cli.main"
        ),
    )
    parser.add_argument(
        "--home",
        type=Path,
        help=(
            "DATA_DESIGNER_HOME to use for the capture. If omitted, a temporary isolated "
            "home is created and deleted after capture."
        ),
    )
    parser.add_argument("--output", type=Path, help="Write JSON capture output to this file instead of stdout.")
    return parser.parse_args()


def resolve_cli(cli: list[str] | None) -> list[str]:
    if cli:
        return cli
    if shutil.which("data-designer") is not None:
        return ["data-designer"]
    return [sys.executable, "-m", "data_designer.cli.main"]


@contextmanager
def resolved_home(home: Path | None) -> Iterator[tuple[Path, str]]:
    if home is not None:
        yield home.expanduser().resolve(), "provided"
        return
    with tempfile.TemporaryDirectory(prefix="data-designer-agent-context-") as tmpdir:
        yield Path(tmpdir), "temporary"


def run_capture(label: str, base_cli: list[str], args: tuple[str, ...], env: dict[str, str]) -> dict[str, Any]:
    argv = [*base_cli, *args]
    try:
        completed = subprocess.run(argv, capture_output=True, check=False, env=env, text=True)
    except FileNotFoundError as exc:
        return {"label": label, "argv": argv, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except OSError as exc:
        return {"label": label, "argv": argv, "returncode": 127, "stdout": "", "stderr": str(exc)}
    return {
        "label": label,
        "argv": argv,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    args = parse_args()
    base_cli = resolve_cli(args.cli)

    with resolved_home(args.home) as (home, home_mode):
        env = os.environ.copy()
        env["DATA_DESIGNER_HOME"] = str(home)
        captures = [run_capture(label, base_cli, command_args, env) for label, command_args in CAPTURE_COMMANDS]
        payload = {
            "cli_prefix": base_cli,
            "data_designer_home": str(home),
            "data_designer_home_mode": home_mode,
            "all_ok": all(capture["returncode"] == 0 for capture in captures),
            "captures": captures,
        }

    output = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

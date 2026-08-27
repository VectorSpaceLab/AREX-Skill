#!/usr/bin/env python3
"""Safe Kedro CLI and project-detection probe."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


_TIMEOUT_SECONDS = 20


def _status(ok: bool, label: str, detail: str = "") -> None:
    prefix = "PASS" if ok else "WARN"
    message = f"{prefix} {label}"
    if detail:
        message += f": {detail}"
    print(message)


def _run_command(command: list[str], env: dict[str, str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            env=env,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return False, "command not found"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {_TIMEOUT_SECONDS}s"

    output = (completed.stdout or completed.stderr or "").strip()
    first_line = output.splitlines()[0] if output else "no output"
    return completed.returncode == 0, first_line


def _looks_like_kedro_project(path: Path) -> tuple[bool, str]:
    current = path.resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        pyproject = candidate / "pyproject.toml"
        if not pyproject.is_file():
            continue
        try:
            text = pyproject.read_text(encoding="utf-8")
        except OSError as exc:
            return False, f"could not read {pyproject.name}: {exc}"
        if "[tool.kedro]" in text:
            return True, str(candidate)
    return False, "no parent pyproject.toml with [tool.kedro]"


def _build_env(disable_telemetry: bool) -> dict[str, str]:
    env = os.environ.copy()
    if disable_telemetry:
        env.setdefault("KEDRO_DISABLE_TELEMETRY", "1")
    return env


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe Kedro CLI probes and inspect whether the current working "
            "directory appears to be inside a Kedro project."
        )
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=Path.cwd(),
        help="Directory to inspect for Kedro project detection. Defaults to cwd.",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Also run `kedro info`, which is read-only but may load plugin metadata.",
    )
    parser.add_argument(
        "--allow-telemetry",
        action="store_true",
        help="Do not set KEDRO_DISABLE_TELEMETRY=1 for subprocess probes.",
    )
    args = parser.parse_args()

    env = _build_env(disable_telemetry=not args.allow_telemetry)
    kedro_exe = shutil.which("kedro")
    if kedro_exe:
        _status(True, "kedro executable", kedro_exe)
        commands = [[kedro_exe, "--version"], [kedro_exe, "--help"]]
        if args.info:
            commands.append([kedro_exe, "info"])
    else:
        _status(False, "kedro executable", "not found on PATH; trying python -m kedro")
        commands = [[sys.executable, "-m", "kedro", "--version"], [sys.executable, "-m", "kedro", "--help"]]
        if args.info:
            commands.append([sys.executable, "-m", "kedro", "info"])

    overall_ok = True
    for command in commands:
        ok, detail = _run_command(command, env)
        overall_ok = overall_ok and ok
        _status(ok, " ".join(command), detail)

    project_ok, project_detail = _looks_like_kedro_project(args.cwd)
    _status(project_ok, "kedro project detection", project_detail)

    if not args.allow_telemetry:
        _status(True, "telemetry opt-out", "KEDRO_DISABLE_TELEMETRY=1 used for probes")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

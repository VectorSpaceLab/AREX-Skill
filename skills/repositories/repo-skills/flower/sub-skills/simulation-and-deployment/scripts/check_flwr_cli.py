#!/usr/bin/env python3
"""Safe help/version/config probe for Flower CLI surfaces."""

from __future__ import annotations

import os
import subprocess
import tempfile
from collections.abc import Sequence
from shutil import which

HELP_CHECKS: list[tuple[list[str], list[str]]] = [
    (
        ["flwr", "--help"],
        [
            "flwr is the Flower command line interface.",
            "new",
            "run",
            "build",
            "install",
            "log",
            "list",
            "stop",
            "login",
            "pull",
            "supernode",
            "app",
            "federation",
            "config",
        ],
    ),
    (["flwr", "run", "--help"], ["@account_name/app_name", "--stream", "--federation-config"]),
    (["flwr", "list", "--help"], ["--run-id", "--limit"]),
    (["flwr", "log", "--help"], ["--stream", "--show"]),
    (["flwr", "stop", "--help"], ["Stop a Flower run", "--format"]),
    (["flwr", "login", "--help"], ["Login to Flower SuperLink"]),
    (["flwr", "pull", "--help"], ["Pull artifacts from a Flower run"]),
    (["flwr", "build", "--help"], ["Build a Flower App into a Flower App Bundle"]),
    (["flwr", "install", "--help"], ["Install a Flower App Bundle"]),
    (["flwr", "config", "--help"], ["Manage Configuration", "list"]),
    (["flwr", "supernode", "--help"], ["register", "unregister", "list"]),
    (["flwr", "federation", "--help"], ["simulation-config", "create", "invite"]),
    (
        ["flwr", "federation", "simulation-config", "--help"],
        [
            "--num-supernodes",
            "CPUs assigned to the",
            "Ratio of a GPU VRAM",
            "--init-args-num-cpus",
            "--init-args-num-gpus",
            "--backend-name",
        ],
    ),
    (
        ["flower-superlink", "--help"],
        [
            "Start a Flower SuperLink",
            "--insecure",
            "--control-api-address",
            "--serverappio-api-address",
            "--simulation",
        ],
    ),
    (
        ["flower-supernode", "--help"],
        [
            "Start a Flower SuperNode",
            "--insecure",
            "--superlink",
            "--clientappio-api-address",
            "--node-config",
        ],
    ),
    (["flwr-datasets", "--help"], ["flwr-datasets is the Flower Datasets command line interface.", "create"]),
]

VERSION_COMMANDS = {
    "flwr": "Flower version:",
    "flower-superlink": "Flower version:",
    "flower-supernode": "Flower version:",
    "flwr-datasets": "Flower Datasets version:",
}


def _run(command: Sequence[str], *, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(command, capture_output=True, text=True, env=env)
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise SystemExit(
            f"Command failed with exit code {proc.returncode}: {' '.join(command)}\n"
            f"{output}"
        )
    return output


def _require_all(label: str, output: str, needles: Sequence[str]) -> None:
    missing = [needle for needle in needles if needle not in output]
    if missing:
        raise SystemExit(
            f"{label} is missing expected text: {', '.join(missing)}\n{output}"
        )


def _make_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def _check_command(command: list[str], needles: Sequence[str], *, env: dict[str, str] | None = None) -> str:
    executable = command[0]
    if which(executable) is None:
        raise SystemExit(f"Command not found on PATH: {executable}")
    output = _run(command, env=env)
    _require_all(" ".join(command), output, needles)
    return output


def main() -> int:
    env = _make_env()

    versions: dict[str, str] = {}
    for executable, prefix in VERSION_COMMANDS.items():
        if which(executable) is None:
            raise SystemExit(f"Command not found on PATH: {executable}")
        output = _run([executable, "--version"], env=env)
        _require_all(f"{executable} --version", output, [prefix])
        version_line = next(
            (line for line in output.splitlines() if prefix in line),
            output.strip().splitlines()[-1],
        )
        versions[executable] = version_line.strip()

    for command, needles in HELP_CHECKS:
        _check_command(command, needles, env=env)

    with tempfile.TemporaryDirectory(prefix="flower-cli-smoke-") as tmpdir:
        config_env = env.copy()
        config_env["FLWR_HOME"] = tmpdir
        config_output = _run(["flwr", "config", "list"], env=config_env)
        _require_all(
            "flwr config list",
            config_output,
            ["Flower Config file:", "supergrid", "local (default)"],
        )

    print("Flower CLI probe passed.")
    for executable in ("flwr", "flower-superlink", "flower-supernode", "flwr-datasets"):
        print(f"- {executable}: {versions[executable]}")
    print("- flwr config list: local (default) profile visible in isolated FLWR_HOME")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

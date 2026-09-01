#!/usr/bin/env python3
"""Run bounded, read-only help probes for a trusted installed ``hf`` CLI.

The checker accepts only exact allowlisted built-in command paths, appends
``--help`` to every probe, uses argv rather than a shell, captures stdout/stderr
separately, and disables startup update checks by default. It intentionally
rejects positional arguments, options, shell metacharacters, other executable
names, unknown paths, unbounded probe counts, and non-finite or excessive
timeouts.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

DEFAULT_PROBES = (
    (),
    ("auth",),
    ("download",),
    ("upload",),
    ("repos",),
    ("buckets", "sync"),
    ("extensions",),
    ("skills",),
)
def _command_paths(prefix: tuple[str, ...], *names: str) -> set[tuple[str, ...]]:
    return {(*prefix, name) for name in names}


SAFE_PROBE_PATHS = frozenset(
    _command_paths(
        (),
        "auth",
        "buckets",
        "cache",
        "collections",
        "cp",
        "datasets",
        "discussions",
        "download",
        "endpoints",
        "env",
        "ext",
        "extensions",
        "jobs",
        "models",
        "papers",
        "repo",
        "repos",
        "sandbox",
        "skills",
        "spaces",
        "sync",
        "update",
        "upload",
        "upload-large-folder",
        "version",
        "webhooks",
    )
    | _command_paths(("auth",), "list", "ls", "login", "logout", "switch", "token", "whoami")
    | _command_paths(
        ("buckets",),
        "cp",
        "create",
        "delete",
        "info",
        "list",
        "ls",
        "move",
        "remove",
        "rm",
        "settings",
        "sync",
    )
    | _command_paths(("cache",), "list", "ls", "prune", "rm", "verify")
    | _command_paths(
        ("collections",),
        "add-item",
        "create",
        "delete",
        "delete-item",
        "info",
        "list",
        "ls",
        "update",
        "update-item",
    )
    | _command_paths(("datasets",), "card", "info", "leaderboard", "list", "ls", "parquet", "sql")
    | _command_paths(
        ("discussions",),
        "close",
        "comment",
        "create",
        "diff",
        "edit",
        "info",
        "list",
        "ls",
        "merge",
        "rename",
        "reopen",
    )
    | _command_paths(
        ("endpoints",),
        "catalog",
        "delete",
        "deploy",
        "describe",
        "hardware",
        "list",
        "list-catalog",
        "pause",
        "resume",
        "scale-to-zero",
        "update",
    )
    | _command_paths(("endpoints", "catalog"), "deploy", "list", "ls")
    | _command_paths(("extensions",), "exec", "install", "list", "ls", "remove", "rm", "search", "update")
    | _command_paths(
        ("jobs",),
        "cancel",
        "hardware",
        "inspect",
        "labels",
        "list",
        "logs",
        "ls",
        "ps",
        "run",
        "scheduled",
        "ssh",
        "stats",
        "uv",
        "wait",
    )
    | _command_paths(
        ("jobs", "scheduled"),
        "delete",
        "inspect",
        "labels",
        "list",
        "ls",
        "ps",
        "resume",
        "run",
        "suspend",
        "trigger",
        "uv",
    )
    | {("jobs", "scheduled", "uv", "run"), ("jobs", "uv", "run")}
    | _command_paths(("models",), "card", "info", "list", "ls")
    | _command_paths(("papers",), "info", "list", "ls", "read", "search")
    | {
        (prefix, name)
        for prefix in ("repo", "repos")
        for name in (
            "branch",
            "cp",
            "create",
            "delete",
            "delete-files",
            "duplicate",
            "list",
            "ls",
            "move",
            "settings",
            "tag",
        )
    }
    | {
        (prefix, group, name)
        for prefix in ("repo", "repos")
        for group, names in (("branch", ("create", "delete")), ("tag", ("create", "delete", "list", "ls")))
        for name in names
    }
    | _command_paths(("sandbox",), "cp", "create", "exec", "kill", "pool", "process", "spawn")
    | _command_paths(("sandbox", "pool"), "create", "delete", "list", "ls", "rm")
    | _command_paths(("sandbox", "process"), "kill", "list", "ls")
    | _command_paths(("skills",), "add", "list", "ls", "preview", "update")
    | _command_paths(
        ("spaces",),
        "card",
        "dev-mode",
        "hardware",
        "hot-reload",
        "info",
        "list",
        "logs",
        "ls",
        "pause",
        "restart",
        "secrets",
        "settings",
        "ssh",
        "templates",
        "variables",
        "volumes",
        "wait",
    )
    | {
        ("spaces", resource, name)
        for resource in ("secrets", "variables")
        for name in ("add", "delete", "list", "ls")
    }
    | _command_paths(("spaces", "volumes"), "delete", "list", "ls", "set")
    | _command_paths(("webhooks",), "create", "delete", "disable", "enable", "info", "list", "ls", "update")
)
COMMAND_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MAX_TIMEOUT_SECONDS = 60.0
MAX_TOTAL_TIMEOUT_SECONDS = 300.0
MAX_CUSTOM_PROBES = 32
MAX_PROBE_DEPTH = 8
MAX_TOKEN_LENGTH = 64


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--executable",
        default="hf",
        help="Trusted hf executable or path to probe (default: hf).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help=f"Seconds per probe, greater than 0 and at most {MAX_TIMEOUT_SECONDS:g} (default: 5).",
    )
    parser.add_argument(
        "--probe",
        action="append",
        metavar="COMMAND_PATH",
        help=(
            "Additional allowlisted command path, e.g. 'models ls'; "
            "arguments, options, and shell syntax are rejected."
        ),
    )
    return parser.parse_args()


def resolve_executable(value: str) -> str:
    path = Path(value).expanduser()
    if path.parent != Path(".") or path.is_absolute():
        if not path.is_file():
            raise ValueError(f"executable not found: {value}")
        resolved = str(path)
    else:
        found = shutil.which(value)
        if found is None:
            raise ValueError(f"executable not found on PATH: {value}")
        resolved = found

    if Path(resolved).name not in {"hf", "hf.exe"}:
        raise ValueError("--executable must resolve to a trusted executable named 'hf' (or 'hf.exe')")
    if not os.access(resolved, os.X_OK):
        raise ValueError(f"executable is not runnable: {value}")
    return resolved


def parse_probe(value: str) -> tuple[str, ...]:
    parts = tuple(value.split())
    if not parts:
        raise ValueError("--probe cannot be empty")
    if len(parts) > MAX_PROBE_DEPTH:
        raise ValueError(f"--probe supports at most {MAX_PROBE_DEPTH} command-name tokens")
    for part in parts:
        if len(part) > MAX_TOKEN_LENGTH or COMMAND_TOKEN.fullmatch(part) is None:
            raise ValueError(f"invalid command-name token in --probe: {part!r}")
    if parts not in SAFE_PROBE_PATHS:
        raise ValueError(f"unsafe, unknown, or non-allowlisted command path in --probe: {value!r}")
    return parts


def run_probe(executable: str, command: tuple[str, ...], timeout: float, env: dict[str, str]) -> int:
    argv = [executable, *command, "--help"]
    label = " ".join(command) or "(top-level)"
    print(f"== hf {label} --help ==", file=sys.stderr)
    try:
        process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            start_new_session=os.name == "posix",
        )
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.communicate()
        print(f"FAIL timeout after {timeout:g}s: {' '.join(argv)}", file=sys.stderr)
        return 124
    except OSError as error:
        print(f"FAIL could not execute {' '.join(argv)}: {error}", file=sys.stderr)
        return 127

    if stdout:
        print(stdout, end="")
    if stderr:
        print(stderr, end="", file=sys.stderr)
    if process.returncode:
        print(f"FAIL exit={process.returncode}: {' '.join(argv)}", file=sys.stderr)
        return process.returncode
    print(f"PASS exit=0: {' '.join(argv)}", file=sys.stderr)
    return 0


def main() -> int:
    args = parse_args()
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= MAX_TIMEOUT_SECONDS:
        print(f"--timeout must be finite, greater than zero, and at most {MAX_TIMEOUT_SECONDS:g}", file=sys.stderr)
        return 2

    custom_probe_values = args.probe or []
    if len(custom_probe_values) > MAX_CUSTOM_PROBES:
        print(f"at most {MAX_CUSTOM_PROBES} custom --probe values are allowed", file=sys.stderr)
        return 2

    try:
        custom_probes = [parse_probe(value) for value in custom_probe_values]
        executable = resolve_executable(args.executable)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    env = os.environ.copy()
    env["HF_HUB_DISABLE_UPDATE_CHECK"] = "1"

    probes = list(DEFAULT_PROBES)
    probes.extend(custom_probes)
    if len(probes) * args.timeout > MAX_TOTAL_TIMEOUT_SECONDS:
        print(
            f"probe count × timeout must not exceed {MAX_TOTAL_TIMEOUT_SECONDS:g} seconds",
            file=sys.stderr,
        )
        return 2

    failures = 0
    for command in probes:
        status = run_probe(executable, command, args.timeout, env)
        if status:
            failures += 1

    print(f"{len(probes) - failures}/{len(probes)} help probes passed", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

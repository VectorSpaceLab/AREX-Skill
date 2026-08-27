#!/usr/bin/env python3
"""Check a DeePMD-kit Python/CLI environment without using source-tree paths."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class BackendProbe:
    key: str
    module: str
    help_alias: str
    display: str


BACKENDS: dict[str, BackendProbe] = {
    "tensorflow": BackendProbe("tensorflow", "tensorflow", "tf", "TensorFlow"),
    "tf": BackendProbe("tensorflow", "tensorflow", "tf", "TensorFlow"),
    "pytorch": BackendProbe("pytorch", "torch", "pt", "PyTorch"),
    "pt": BackendProbe("pytorch", "torch", "pt", "PyTorch"),
    "jax": BackendProbe("jax", "jax", "jax", "JAX"),
    "paddle": BackendProbe("paddle", "paddle", "pd", "Paddle"),
    "pd": BackendProbe("paddle", "paddle", "pd", "Paddle"),
    "pytorch-exportable": BackendProbe(
        "pytorch-exportable", "torch", "pt-expt", "PyTorch exportable"
    ),
    "pt-expt": BackendProbe(
        "pytorch-exportable", "torch", "pt-expt", "PyTorch exportable"
    ),
}

ALL_BACKEND_KEYS = ("tensorflow", "pytorch", "jax", "paddle", "pytorch-exportable")


class ResultCounter:
    def __init__(self) -> None:
        self.failures = 0
        self.warnings = 0

    def pass_(self, message: str) -> None:
        print(f"PASS {message}")

    def warn(self, message: str) -> None:
        self.warnings += 1
        print(f"WARN {message}")

    def fail(self, message: str) -> None:
        self.failures += 1
        print(f"FAIL {message}")


def import_version(module_name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - show actionable import failure
        return False, f"{exc.__class__.__name__}: {exc}"
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = importlib.metadata.version(module_name)
        except importlib.metadata.PackageNotFoundError:
            version = "version unknown"
    return True, str(version)


def run_command(command: list[str], timeout: int) -> tuple[int | None, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return None, "command not found"
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        return None, f"timed out after {timeout}s\n{partial}".strip()
    return completed.returncode, completed.stdout.strip()


def normalized_backends(selected: Iterable[str]) -> list[BackendProbe]:
    probes: list[BackendProbe] = []
    seen: set[str] = set()
    for item in selected:
        if item == "all":
            names = ALL_BACKEND_KEYS
        else:
            names = (item,)
        for name in names:
            probe = BACKENDS[name]
            if probe.key not in seen:
                probes.append(probe)
                seen.add(probe.key)
    return probes


def print_command_hint(command: list[str]) -> str:
    return " ".join(command)


def check_python(counter: ResultCounter) -> None:
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro}"
    if version >= (3, 10):
        counter.pass_(f"Python {version_text} satisfies DeePMD-kit Python >=3.10")
    else:
        counter.fail(
            f"Python {version_text} is unsupported; create a Python 3.10+ environment"
        )


def check_deepmd_import(counter: ResultCounter) -> None:
    ok, detail = import_version("deepmd")
    if ok:
        try:
            dist_version = importlib.metadata.version("deepmd-kit")
        except importlib.metadata.PackageNotFoundError:
            dist_version = "distribution version unknown"
        counter.pass_(f"import deepmd succeeded ({dist_version}; module {detail})")
    else:
        counter.fail(
            "import deepmd failed; install the deepmd-kit distribution in this Python "
            f"environment ({detail})"
        )


def check_extra_module(counter: ResultCounter, module_name: str) -> None:
    ok, detail = import_version(module_name)
    if ok:
        counter.pass_(f"import {module_name} succeeded ({detail})")
    else:
        counter.warn(f"import {module_name} failed ({detail})")


def check_dp(counter: ResultCounter, timeout: int) -> bool:
    dp_path = shutil.which("dp")
    if dp_path is None:
        counter.fail("dp command not found on PATH; activate the install environment")
        return False
    counter.pass_(f"dp command found at {dp_path}")

    for command in (["dp", "--version"], ["dp", "-h"]):
        returncode, output = run_command(command, timeout)
        command_text = print_command_hint(command)
        if returncode == 0:
            first_line = output.splitlines()[0] if output else "no output"
            counter.pass_(f"{command_text} succeeded ({first_line})")
        else:
            detail = output.splitlines()[-1] if output else "no output"
            counter.fail(f"{command_text} failed ({detail})")
    return True


def check_backend_module(counter: ResultCounter, probe: BackendProbe, strict: bool) -> None:
    ok, detail = import_version(probe.module)
    if ok:
        counter.pass_(f"{probe.display} module {probe.module!r} import succeeded ({detail})")
        return
    message = (
        f"{probe.display} module {probe.module!r} import failed ({detail}); "
        f"install the {probe.display} backend package or choose another backend"
    )
    if strict:
        counter.fail(message)
    else:
        counter.warn(message)


def check_backend_help(counter: ResultCounter, probe: BackendProbe, timeout: int) -> None:
    command = ["dp", f"--{probe.help_alias}", "-h"]
    returncode, output = run_command(command, timeout)
    command_text = print_command_hint(command)
    if returncode == 0:
        counter.pass_(f"{command_text} succeeded")
    else:
        detail = output.splitlines()[-1] if output else "no output"
        counter.warn(
            f"{command_text} failed ({detail}); confirm the CLI alias and backend install"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a DeePMD-kit runtime environment with safe import and CLI "
            "checks. The script does not read the DeePMD-kit source tree."
        )
    )
    parser.add_argument(
        "--backend",
        action="append",
        choices=["all", *BACKENDS.keys()],
        default=[],
        help=(
            "Backend to check. May be repeated. Use 'all' for TensorFlow, PyTorch, "
            "JAX, Paddle, and PyTorch exportable probes."
        ),
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Additional Python module to import-check. May be repeated.",
    )
    parser.add_argument(
        "--check-backend-help",
        action="store_true",
        help="Run dp --<backend-alias> -h for each selected backend.",
    )
    parser.add_argument(
        "--skip-dp",
        action="store_true",
        help="Skip dp command discovery and dp help/version checks.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat selected backend import warnings as failures.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Seconds to wait for each dp subprocess check.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    counter = ResultCounter()

    check_python(counter)
    check_deepmd_import(counter)
    dp_available = True
    if not args.skip_dp:
        dp_available = check_dp(counter, args.timeout)

    for module_name in args.module:
        check_extra_module(counter, module_name)

    for probe in normalized_backends(args.backend):
        check_backend_module(counter, probe, args.strict)
        if args.check_backend_help:
            if dp_available and not args.skip_dp:
                check_backend_help(counter, probe, args.timeout)
            else:
                counter.warn(
                    f"skipping {probe.display} CLI help because dp command is unavailable"
                )

    if counter.failures:
        print(
            f"SUMMARY {counter.failures} failure(s), {counter.warnings} warning(s). "
            "Fix FAIL lines before using this DeePMD-kit environment."
        )
        return 1
    print(
        f"SUMMARY no failures, {counter.warnings} warning(s). "
        "Review WARN lines for optional backend coverage."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

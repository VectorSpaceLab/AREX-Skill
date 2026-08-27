#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team
"""Safely inspect DeepSpeed operational tools without launching jobs or writing NVMe data."""

from __future__ import annotations

import argparse
import importlib
import inspect
import shutil
import subprocess
import sys
from dataclasses import dataclass


DEFAULT_TOOLS = ("deepspeed", "ds", "ds_report", "ds_io", "ds_nvme_tune")
DEFAULT_IMPORTS = (
    "deepspeed",
    "deepspeed.env_report",
    "deepspeed.autotuning.config",
    "deepspeed.profiling.flops_profiler",
    "deepspeed.monitor.monitor",
    "deepspeed.compression.compress",
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def run_help(tool: str, timeout: float) -> CheckResult:
    executable = shutil.which(tool)
    if executable is None:
        return CheckResult(tool, False, "not found on PATH")

    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(tool, False, f"--help timed out after {timeout:g}s")
    except OSError as error:
        return CheckResult(tool, False, f"failed to execute --help: {error}")

    output = (completed.stdout + completed.stderr).strip().splitlines()
    first_line = output[0] if output else "no help text emitted"
    if completed.returncode == 0:
        return CheckResult(tool, True, first_line)
    return CheckResult(tool, False, f"exit {completed.returncode}: {first_line}")


def import_module(module_name: str) -> CheckResult:
    try:
        module = importlib.import_module(module_name)
    except Exception as error:  # noqa: BLE001 - diagnostic tool should report import failure type.
        return CheckResult(module_name, False, f"{type(error).__name__}: {error}")

    module_file = getattr(module, "__file__", "built-in")
    return CheckResult(module_name, True, f"imported from {module_file}")


def inspect_api() -> list[CheckResult]:
    results: list[CheckResult] = []
    api_targets = (
        ("deepspeed.profiling.flops_profiler", "get_model_profile"),
        ("deepspeed.profiling.flops_profiler", "FlopsProfiler"),
        ("deepspeed.monitor.monitor", "MonitorMaster"),
        ("deepspeed.compression.compress", "init_compression"),
        ("deepspeed.compression.compress", "redundancy_clean"),
    )

    for module_name, attribute in api_targets:
        label = f"{module_name}.{attribute}"
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attribute)
            signature = str(inspect.signature(value))
        except Exception as error:  # noqa: BLE001 - diagnostic tool should report import/introspection failure type.
            results.append(CheckResult(label, False, f"{type(error).__name__}: {error}"))
            continue
        results.append(CheckResult(label, True, signature))

    return results


def print_section(title: str, results: list[CheckResult]) -> bool:
    print(f"\n## {title}")
    all_ok = True
    for result in results:
        status = "OK" if result.ok else "WARN"
        print(f"[{status}] {result.name}: {result.detail}")
        all_ok = all_ok and result.ok
    return all_ok


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Locate DeepSpeed CLI tools, run safe --help checks with timeouts, "
            "and import selected operational APIs. This script does not build ops, "
            "launch training, run SSH, or write NVMe/GDS benchmark data."
        )
    )
    parser.add_argument("--timeout", type=float, default=8.0, help="Seconds allowed for each --help invocation.")
    parser.add_argument(
        "--tool",
        action="append",
        dest="tools",
        help="Tool name to check. May be repeated. Defaults to common DeepSpeed tools.",
    )
    parser.add_argument(
        "--skip-help",
        action="store_true",
        help="Skip CLI --help subprocess checks and only run Python import/API checks.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any tool, import, or API check fails. Default exits zero after reporting warnings.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tools = tuple(args.tools) if args.tools else DEFAULT_TOOLS

    ok = True
    if not args.skip_help:
        help_results = [run_help(tool, args.timeout) for tool in tools]
        ok = print_section("CLI help checks", help_results) and ok

    import_results = [import_module(module_name) for module_name in DEFAULT_IMPORTS]
    ok = print_section("Import checks", import_results) and ok

    api_results = inspect_api()
    ok = print_section("API signature checks", api_results) and ok

    print("\nSafety note: this script intentionally avoids ds_io, ds_nvme_tune workloads, ds_ssh, builds, and training launches.")
    if args.strict and not ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Verify that the installed hivemind package and its common entry points work.

Safe to run from any directory. The script only imports the installed package,
checks the package metadata, and optionally probes CUDA and ALBERT-related
extras. It does not touch the source checkout.

Examples:
  python scripts/check_install.py
  python scripts/check_install.py --check-cuda
  python scripts/check_install.py --check-albert
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence


OPTIONAL_ALBERT_MODULES = (
    "transformers",
    "datasets",
    "torch_optimizer",
    "wandb",
    "sentencepiece",
    "requests",
    "nltk",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str


def _import_and_report(module_name: str) -> CheckResult:
    try:
        __import__(module_name)
    except Exception as exc:  # pragma: no cover - defensive helper
        return CheckResult(module_name, False, f"missing optional dependency: {module_name} ({exc.__class__.__name__}: {exc})")
    return CheckResult(module_name, True, f"import ok: {module_name}")


def _run_help(command: Sequence[str]) -> CheckResult:
    if shutil.which(command[0]) is None:
        return CheckResult(command[0], False, f"missing console script: {command[0]}")

    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
        return CheckResult(command[0], False, f"{command[0]} --help failed: {detail}")
    return CheckResult(command[0], True, f"help ok: {command[0]}")


def _check_cuda() -> CheckResult:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - defensive helper
        return CheckResult("cuda", False, f"missing required dependency for CUDA smoke: torch ({exc.__class__.__name__}: {exc})")

    if not torch.cuda.is_available():
        return CheckResult("cuda", False, "CUDA unavailable in this environment")

    tensor = torch.tensor([1.0], device="cuda")
    torch.cuda.synchronize()
    device_name = torch.cuda.get_device_name(0)
    return CheckResult("cuda", True, f"cuda smoke ok: {tensor.device} on {device_name}")


def _check_albert_optional() -> list[CheckResult]:
    results = [_import_and_report(name) for name in OPTIONAL_ALBERT_MODULES if name != "nltk"]

    try:
        import nltk
    except Exception as exc:  # pragma: no cover - defensive helper
        results.append(CheckResult("nltk", False, f"missing optional dependency: nltk ({exc.__class__.__name__}: {exc})"))
        return results

    results.append(CheckResult("nltk", True, "import ok: nltk"))
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        results.append(
            CheckResult(
                "nltk-punkt",
                True,
                "nltk is installed; punkt corpus will be downloaded by the preprocessing script when needed",
            )
        )
    else:
        results.append(CheckResult("nltk-punkt", True, "nltk punkt corpus is already available"))

    return results


def _print_result(result: CheckResult) -> bool:
    print(result.message)
    return result.ok


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-cuda",
        action="store_true",
        help="Run a minimal CUDA tensor allocation smoke check if CUDA is available.",
    )
    parser.add_argument(
        "--check-albert",
        action="store_true",
        help="Check optional dependencies used by the collaborative ALBERT example workflow.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    failures = 0

    try:
        import hivemind
        import torch
    except Exception as exc:  # pragma: no cover - defensive helper
        print(f"failed to import hivemind or torch: {exc.__class__.__name__}: {exc}")
        return 1

    print(f"hivemind version: {hivemind.__version__}")
    print(f"python version: {sys.version.split()[0]}")
    print(f"torch version: {torch.__version__}")
    print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")
    print(f"torch.cuda.device_count(): {torch.cuda.device_count()}")

    core_imports = ["hivemind.dht", "hivemind.optim", "hivemind.moe", "hivemind.compression"]
    for module_name in core_imports:
        failures += 0 if _print_result(_import_and_report(module_name)) else 1

    if _print_result(_run_help(["hivemind-dht", "--help"])) is False:
        failures += 1
    if _print_result(_run_help(["hivemind-server", "--help"])) is False:
        failures += 1

    if args.check_cuda:
        failures += 0 if _print_result(_check_cuda()) else 1

    if args.check_albert:
        for result in _check_albert_optional():
            failures += 0 if _print_result(result) else 1

    if failures:
        print(f"check_install finished with {failures} failure(s)")
        return 1

    print("check_install finished successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

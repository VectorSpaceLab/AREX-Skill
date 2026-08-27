#!/usr/bin/env python3
"""Safe preflight checks for the Transformers skill.

This script never downloads models, starts servers, or runs training. It checks
imports, optional package availability, console script wiring, and common
workflow dependency expectations so an agent can fail early with actionable
messages.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import sys
from dataclasses import dataclass, asdict


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def check_import(module: str) -> CheckResult:
    try:
        imported = importlib.import_module(module)
    except Exception as error:  # noqa: BLE001 - report exact optional dependency issue.
        return CheckResult(module, False, f"{type(error).__name__}: {error}")
    version = getattr(imported, "__version__", None)
    return CheckResult(module, True, f"version={version}" if version else "imported")


def check_distribution(name: str) -> CheckResult:
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return CheckResult(f"dist:{name}", False, "distribution not installed")
    return CheckResult(f"dist:{name}", True, f"version={dist.version}")


def check_console_script() -> CheckResult:
    executable = shutil.which("transformers")
    if executable:
        return CheckResult("console:transformers", True, "console script found on PATH")
    try:
        eps = metadata.entry_points()
        scripts = eps.select(group="console_scripts", name="transformers")
    except Exception as error:  # noqa: BLE001
        return CheckResult("console:transformers", False, f"entry point query failed: {error}")
    if scripts:
        return CheckResult("console:transformers", True, "entry point installed but executable not on PATH")
    return CheckResult("console:transformers", False, "console script not found")


def collect(args: argparse.Namespace) -> list[CheckResult]:
    results: list[CheckResult] = []

    if args.check_imports or args.all:
        results.append(check_import("transformers"))
        results.append(check_distribution("transformers"))

    if args.check_cli or args.all:
        results.append(check_console_script())
        for module in ["huggingface_hub", "typer", "requests", "httpx", "rich"]:
            results.append(check_import(module))

    if args.check_serving or args.all:
        for module in ["fastapi", "uvicorn", "pydantic", "openai", "starlette"]:
            results.append(check_import(module))

    if args.check_training or args.all:
        for module in ["torch", "accelerate", "datasets", "evaluate"]:
            results.append(check_import(module))

    if args.check_vision or args.all:
        for module in ["PIL", "torchvision"]:
            results.append(check_import(module))

    if args.check_audio or args.all:
        for module in ["torchaudio", "librosa"]:
            results.append(check_import(module))

    if args.check_quantization or args.all:
        for module in ["bitsandbytes", "accelerate", "peft", "torchao"]:
            results.append(check_import(module))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe Transformers skill preflight checks.")
    parser.add_argument("--all", action="store_true", help="Run all check groups.")
    parser.add_argument("--check-imports", action="store_true", help="Check base transformers import and distribution.")
    parser.add_argument("--check-cli", action="store_true", help="Check CLI-related imports and console script wiring.")
    parser.add_argument("--check-serving", action="store_true", help="Check serving optional dependencies.")
    parser.add_argument("--check-training", action="store_true", help="Check training optional dependencies.")
    parser.add_argument("--check-vision", action="store_true", help="Check vision optional dependencies.")
    parser.add_argument("--check-audio", action="store_true", help="Check audio optional dependencies.")
    parser.add_argument("--check-quantization", action="store_true", help="Check common quantization optional dependencies.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    if not any(vars(args).values()):
        args.check_imports = True

    results = collect(args)
    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
    else:
        for result in results:
            status = "OK" if result.ok else "MISSING"
            print(f"{status:7} {result.name}: {result.detail}")

    hard_failures = [result for result in results if not result.ok]
    return 1 if hard_failures else 0


if __name__ == "__main__":
    sys.exit(main())

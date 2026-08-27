#!/usr/bin/env python3
"""Report Mellea backend imports and optional dependency availability.

This diagnostic is read-only: it does not construct a provider backend, start a
service, make a network request, download a model, read credentials, or load a
checkpoint. Run it from any working directory with the target package installed.

Examples:
    python check_backends.py
    python check_backends.py --torch
    python check_backends.py --torch --probe-allocation
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from collections.abc import Iterable

BACKEND_MODULES: tuple[tuple[str, str], ...] = (
    ("ollama", "mellea.backends.ollama"),
    ("openai", "mellea.backends.openai"),
    ("huggingface", "mellea.backends.huggingface"),
    ("litellm", "mellea.backends.litellm"),
    ("watsonx", "mellea.backends.watsonx"),
    ("bedrock helpers", "mellea.backends.bedrock"),
    ("dummy", "mellea.backends.dummy"),
    ("Granite formatters", "mellea.formatters.granite"),
    ("adapter catalog", "mellea.backends.adapters.catalog"),
)

OPTIONAL_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("hf", "torch"),
    ("hf", "transformers"),
    ("hf", "llguidance"),
    ("hf", "peft"),
    ("hf", "huggingface_hub"),
    ("litellm", "litellm"),
    ("litellm", "boto3"),
    ("watsonx", "ibm_watsonx_ai"),
    ("telemetry", "opentelemetry"),
    ("cli", "typer"),
)


def _available(module_name: str) -> bool:
    """Return whether Python can locate a module without importing it."""
    return importlib.util.find_spec(module_name) is not None


def _report_imports() -> int:
    """Import package modules and print a compact status for each one."""
    try:
        package = importlib.import_module("mellea")
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(f"mellea: ERROR {type(exc).__name__}: {exc}")
        return 1

    print(f"mellea: OK version={getattr(package, '__version__', 'unknown')}")
    failures = 0
    for label, module_name in BACKEND_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            print(f"{label}: MISSING optional dependency ({exc})")
        except Exception as exc:  # pragma: no cover - module-specific failures
            failures += 1
            print(f"{label}: ERROR {type(exc).__name__}: {exc}")
        else:
            print(f"{label}: OK ({module_name})")
    return failures


def _report_dependencies() -> None:
    """Print optional dependency discovery without importing those dependencies."""
    print("optional dependencies:")
    for extra, module_name in OPTIONAL_DEPENDENCIES:
        state = "available" if _available(module_name) else "missing"
        print(f"  {extra}: {module_name}: {state}")


def _report_torch(probe_allocation: bool) -> int:
    """Report Torch device facts and optionally attempt one tiny allocation."""
    if not _available("torch"):
        print("torch: missing (install the hf extra for device inspection)")
        return 0
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(f"torch: ERROR {type(exc).__name__}: {exc}")
        return 1

    cuda_available = bool(torch.cuda.is_available())
    print(
        "torch: OK "
        f"version={getattr(torch, '__version__', 'unknown')} "
        f"cuda_available={cuda_available} "
        f"cuda_devices={torch.cuda.device_count() if cuda_available else 0}"
    )
    mps_available = bool(
        getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()
    )
    print(f"torch: mps_available={mps_available}")

    if not probe_allocation:
        print("torch: allocation probe skipped (use --probe-allocation to opt in)")
        return 0
    if not cuda_available:
        print("torch: allocation probe skipped (CUDA unavailable)")
        return 0
    try:
        tensor = torch.zeros(1, device="cuda")
    except Exception as exc:  # A diagnostic result, not a script crash.
        print(
            f"torch: one-element CUDA allocation blocked: {type(exc).__name__}: {exc}"
        )
    else:
        print(f"torch: one-element CUDA allocation OK device={tensor.device}")
        del tensor
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Mellea backend import and optional-dependency diagnostic; "
            "no provider calls, downloads, or service startup."
        )
    )
    parser.add_argument(
        "--torch",
        action="store_true",
        help="also report Torch CUDA/MPS availability (no allocation by default)",
    )
    parser.add_argument(
        "--probe-allocation",
        action="store_true",
        help="with --torch, attempt one tiny CUDA allocation; may report OOM",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run the diagnostic and return a process exit code."""
    args = build_parser().parse_args(argv)
    if args.probe_allocation and not args.torch:
        print("error: --probe-allocation requires --torch", file=sys.stderr)
        return 2
    failures = _report_imports()
    _report_dependencies()
    if args.torch:
        failures += _report_torch(args.probe_allocation)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a safe, read-only Earth2Studio environment preflight.

This bundled helper checks Python support, core importability, optional CUDA
visibility, and explicitly requested imports. It never installs packages,
contacts services, fetches data, or downloads model assets.

Examples:
  python scripts/check_environment.py --help
  python scripts/check_environment.py --json --check-import earth2studio.data
  python scripts/check_environment.py --require-cuda
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any

MIN_PYTHON = (3, 11)
MAX_PYTHON_EXCLUSIVE = (3, 15)


@dataclass
class Check:
    name: str
    ok: bool
    value: Any
    detail: str = ""


def supported_python(version: tuple[int, int]) -> bool:
    """Return whether a major/minor version is in the package's range."""
    return MIN_PYTHON <= version < MAX_PYTHON_EXCLUSIVE


def _import_check(name: str) -> Check:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # optional modules can fail beyond ImportError
        return Check(name, False, None, f"{type(exc).__name__}: {exc}")
    return Check(name, True, getattr(module, "__version__", "imported"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--check-import", action="append", default=[], metavar="MODULE")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true", help="check pure version-range logic without importing the package")
    args = parser.parse_args(argv)
    if args.self_test:
        assert supported_python((3, 13))
        assert not supported_python((3, 10))
        assert not supported_python((3, 15))
        print("self-test: passed")
        return 0

    checks = [
        Check(
            "python",
            supported_python((sys.version_info.major, sys.version_info.minor)),
            f"{sys.version_info.major}.{sys.version_info.minor}",
            "Earth2Studio requires >=3.11,<3.15",
        ),
        _import_check("earth2studio"),
    ]
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        checks.append(Check("torch", False, None, f"{type(exc).__name__}: {exc}"))
        checks.append(Check("cuda", not args.require_cuda, False, "torch unavailable"))
    else:
        available = bool(torch.cuda.is_available())
        checks.append(Check("torch", True, getattr(torch, "__version__", "unknown")))
        checks.append(
            Check(
                "cuda",
                available if args.require_cuda else True,
                available,
                "CUDA available" if available else "CUDA unavailable (not required)",
            )
        )
    checks.extend(_import_check(name) for name in args.check_import)
    payload = {
        "checks": [asdict(check) for check in checks],
        "offline": True,
        "network_or_install_actions": False,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        for check in checks:
            print(f"{'PASS' if check.ok else 'FAIL'} {check.name}: {check.value} {check.detail}")
        print("offline: no installation, network, data fetch, or checkpoint load")
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

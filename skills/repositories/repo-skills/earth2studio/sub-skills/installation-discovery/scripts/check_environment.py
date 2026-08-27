#!/usr/bin/env python3
"""Run an offline, read-only Earth2Studio environment preflight.

This helper checks the supported Python range, core package importability,
optional CUDA visibility, and explicitly requested imports. It never installs
packages, contacts services, fetches data, or downloads model assets.
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
    """Return whether a major/minor version is supported."""
    return MIN_PYTHON <= version < MAX_PYTHON_EXCLUSIVE


def _import_check(name: str) -> Check:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return Check(name, False, None, f"{type(exc).__name__}: {exc}")
    return Check(name, True, getattr(module, "__version__", "imported"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--check-import", action="append", default=[], metavar="MODULE")
    parser.add_argument("--python-version", metavar="VERSION", help="offline range-test override")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        assert supported_python((3, 13)) and not supported_python((3, 10))
        print("self-test: passed")
        return 0
    version = (sys.version_info.major, sys.version_info.minor)
    if args.python_version:
        try:
            parts = tuple(int(part) for part in args.python_version.split(".")[:2])
            if len(parts) != 2: raise ValueError
            version = parts  # type: ignore[assignment]
        except ValueError:
            parser.error("--python-version must look like 3.13")
    checks = [Check("python", supported_python(version), f"{version[0]}.{version[1]}", "requires >=3.11,<3.15"), _import_check("earth2studio")]
    try:
        torch = importlib.import_module("torch")
    except Exception as exc:
        checks.append(Check("torch", False, None, f"{type(exc).__name__}: {exc}"))
        checks.append(Check("cuda", not args.require_cuda, False, "torch unavailable"))
    else:
        available = bool(torch.cuda.is_available())
        checks.extend([Check("torch", True, getattr(torch, "__version__", "unknown")), Check("cuda", available if args.require_cuda else True, available)])
    checks.extend(_import_check(name) for name in args.check_import)
    payload = {"checks": [asdict(check) for check in checks], "offline": True, "network_or_install_actions": False}
    if args.json: print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        for check in checks: print(f"{'PASS' if check.ok else 'FAIL'} {check.name}: {check.value} {check.detail}")
        print("offline: no installation, network, data fetch, or checkpoint load")
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

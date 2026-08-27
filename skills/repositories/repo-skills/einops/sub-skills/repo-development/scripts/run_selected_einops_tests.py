#!/usr/bin/env python3
"""Dry-run-first wrapper for selected einops native tests.

This helper mirrors the public repository test runner semantics while making the
backend environment variable and focused pytest command visible before anything
executes. It depends on an installed `einops` package and pytest when --execute
is used.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SYNONYMS = {"pytorch": "torch", "tf": "tensorflow", "paddlepaddle": "paddle"}
KNOWN = {
    "numpy",
    "torch",
    "jax",
    "tensorflow",
    "cupy",
    "paddle",
    "oneflow",
    "pytensor",
    "mlx.core",
}
INSTALLS = {
    "numpy": ["numpy"],
    "torch": ["torch --index-url https://download.pytorch.org/whl/cpu"],
    "jax": ["jax[cpu]", "flax"],
    "tensorflow": ["tensorflow"],
    "cupy": ["cupy"],
    "paddle": ["paddlepaddle"],
    "oneflow": ["oneflow==0.9.0"],
    "pytensor": ["pytensor"],
    "mlx.core": ["mlx or mlx[cpu], depending on platform"],
}


def normalize(names: list[str]) -> list[str]:
    normalized: list[str] = []
    for name in names:
        for part in name.replace(",", " ").split():
            backend = SYNONYMS.get(part, part)
            if backend not in KNOWN:
                raise SystemExit(f"Unrecognized framework {part!r}; known values: {sorted(KNOWN)}")
            normalized.append(backend)
    if not normalized:
        raise SystemExit("At least one backend is required, e.g. numpy.")
    return normalized


def installed_tests_dir() -> Path:
    try:
        import einops.tests as tests  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit("Cannot import einops.tests; install einops before running this helper.") from exc
    return Path(tests.__file__).resolve().parent


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Plan or run selected einops native tests with backend selection.")
    p.add_argument("frameworks", nargs="+", help="Backend names, e.g. numpy, pytorch, tensorflow, jax, mlx.core.")
    p.add_argument("--pytest-target", help="Focused pytest node relative to installed einops.tests, e.g. test_ops.py::test_repeat_numpy.")
    p.add_argument("--pip-install", action="store_true", help="Show/install native runner dependency packages. Mutates the current environment when --execute is set.")
    p.add_argument("--execute", action="store_true", help="Actually run pip installs (if requested) and pytest. Default is dry-run only.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    frameworks = normalize(args.frameworks)
    env_value = ",".join(frameworks)
    tests_dir = installed_tests_dir()
    target = args.pytest_target or "."
    cmd = [sys.executable, "-m", "pytest", target]

    print("Selected backends:", " ".join(frameworks))
    print("EINOPS_TEST_BACKENDS=", env_value, sep="")
    print("Installed tests dir:", tests_dir)
    print("Pytest command:", " ".join(cmd))

    if args.pip_install:
        print("Requested --pip-install. Packages that native runner would install:")
        print("  pytest")
        for backend in frameworks:
            for item in INSTALLS.get(backend, []):
                print(" ", item)
        if not args.execute:
            print("Dry-run only: no packages were installed.")

    if not args.execute:
        print("Dry-run only. Add --execute to run the planned command.")
        return 0

    if args.pip_install:
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "--progress-bar", "off", "-q"], check=True)
        for backend in frameworks:
            for instruction in INSTALLS.get(backend, []):
                if " or " in instruction:
                    print(f"SKIP install hint for {backend}: {instruction}")
                    continue
                subprocess.run([sys.executable, "-m", "pip", "install", *instruction.split(), "--progress-bar", "off", "-q"], check=True)

    env = {**os.environ, "EINOPS_TEST_BACKENDS": env_value}
    result = subprocess.run(cmd, cwd=tests_dir, env=env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

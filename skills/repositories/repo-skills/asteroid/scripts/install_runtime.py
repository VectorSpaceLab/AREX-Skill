#!/usr/bin/env python3
"""Self-contained Asteroid runtime bootstrap.

This helper installs the public Asteroid runtime package and the extra runtime
packages that the generated skill inspection found were needed for the
pretrained/inference and dataset-import paths.

It does not depend on the original source checkout.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


RUNTIME_REQUIREMENTS = Path(__file__).with_name("runtime_requirements.txt")


def run(cmd: list[str], *, cwd: str | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)


def pip_cmd(python: str, *args: str) -> list[str]:
    return [python, "-m", "pip", *args]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable that should receive the runtime packages.",
    )
    parser.add_argument(
        "--index-url",
        default=None,
        help="Optional primary pip package index URL or mirror.",
    )
    parser.add_argument(
        "--extra-index-url",
        action="append",
        default=[],
        help="Optional extra pip index URL; repeat for multiple indexes.",
    )
    parser.add_argument(
        "--requirements",
        default=str(RUNTIME_REQUIREMENTS),
        help="Self-contained runtime requirements file to install.",
    )
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        help="Additional package specifier to install; repeat for multiple extras.",
    )
    parser.add_argument(
        "--with-tests",
        action="store_true",
        help="Also install pytest for local repo-test runs.",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip the post-install import and pip-check verification.",
    )
    parser.add_argument(
        "--no-upgrade-tools",
        action="store_true",
        help="Do not upgrade pip/setuptools/wheel before installing runtime packages.",
    )
    args = parser.parse_args()

    python = args.python
    base = pip_cmd(python)

    if not args.no_upgrade_tools:
        run(base + ["install", "--upgrade", "pip", "setuptools", "wheel"])

    install = base + ["install"]
    if args.index_url:
        install += ["--index-url", args.index_url]
    for url in args.extra_index_url:
        install += ["--extra-index-url", url]

    requirements_path = Path(args.requirements).expanduser()
    if not requirements_path.is_file():
        raise SystemExit(f"Runtime requirements file not found: {requirements_path}")

    install_args = install + ["-r", str(requirements_path)]
    if args.with_tests:
        install_args.append("pytest")
    install_args.extend(args.package)

    run(install_args)
    run(base + ["check"])

    if not args.skip_verify:
        verify_dir = tempfile.mkdtemp(prefix="asteroid-runtime-verify-")
        code = (
            "import asteroid, requests, librosa, torch, torchaudio; "
            "import asteroid.data, asteroid.engine.system, asteroid.losses; "
            "print('asteroid', asteroid.__version__); "
            "print('torch', torch.__version__); "
            "print('torchaudio', torchaudio.__version__); "
            "print('librosa', librosa.__version__)"
        )
        run([python, "-I", "-c", code], cwd=verify_dir)

    print("Asteroid runtime bootstrap complete.")


if __name__ == "__main__":
    main()

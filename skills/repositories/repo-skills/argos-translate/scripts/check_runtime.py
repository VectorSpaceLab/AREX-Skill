#!/usr/bin/env python3
"""Inspect an installed Argos Translate runtime.

Run from the Python environment that should use Argos Translate:

    python scripts/check_runtime.py
    python scripts/check_runtime.py --check-cli

The script imports the public modules, prints verified signatures, and runs a
small IdentityTranslation smoke test. It does not download packages, call remote
services, or require an original source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def print_signature(label: str, obj) -> None:
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError) as exc:
        print(f"{label}: signature unavailable ({exc})")
    else:
        print(f"{label}: {signature}")


def run_cli_help(command: str) -> bool:
    executable = shutil.which(command)
    if executable is None:
        print(f"{command}: not found on PATH")
        return False
    completed = subprocess.run(
        [command, "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    first_line = (completed.stdout or completed.stderr).splitlines()[0:1]
    print(f"{command}: exit={completed.returncode}; {first_line[0] if first_line else 'no output'}")
    return completed.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check an installed Argos Translate runtime.")
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help="Also run argos-translate --help and argospm --help if commands are on PATH.",
    )
    args = parser.parse_args(argv)

    try:
        dist_version = version("argostranslate")
    except PackageNotFoundError:
        return fail("distribution 'argostranslate' is not installed in this Python environment")

    print(f"argostranslate distribution: {dist_version}")

    module_names = [
        "argostranslate",
        "argostranslate.package",
        "argostranslate.translate",
        "argostranslate.cli",
        "argostranslate.argospm",
        "argostranslate.settings",
    ]
    modules = {}
    for name in module_names:
        try:
            modules[name] = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - diagnostic helper should report any import failure.
            return fail(f"failed to import {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"import ok: {name}")

    package = modules["argostranslate.package"]
    translate = modules["argostranslate.translate"]
    cli = modules["argostranslate.cli"]
    argospm = modules["argostranslate.argospm"]
    settings = modules["argostranslate.settings"]

    print_signature("package.install_from_path", package.install_from_path)
    print_signature("package.get_installed_packages", package.get_installed_packages)
    print_signature("translate.get_installed_languages", translate.get_installed_languages)
    print_signature("translate.translate", translate.translate)
    print_signature("cli.main", cli.main)
    print_signature("argospm.main", argospm.main)

    try:
        language = translate.Language("en", "English")
        identity = translate.IdentityTranslation(language)
        smoke = identity.translate("Hello")
    except Exception as exc:  # noqa: BLE001
        return fail(f"IdentityTranslation smoke failed: {type(exc).__name__}: {exc}")
    if smoke != "Hello":
        return fail(f"IdentityTranslation returned unexpected value: {smoke!r}")
    print("IdentityTranslation smoke: ok")

    print(f"settings.device: {settings.device}")
    print(f"settings.chunk_type: {settings.chunk_type}")
    print(f"installed model package count: {len(package.get_installed_packages())}")

    if args.check_cli:
        ok = run_cli_help("argos-translate") and run_cli_help("argospm")
        if not ok:
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

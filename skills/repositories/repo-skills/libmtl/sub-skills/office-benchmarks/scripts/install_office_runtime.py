#!/usr/bin/env python3
"""Install the self-contained Office benchmark runtime package.

This installs the bundled `libmtl_office_benchmark` source package so the
Office workflow can run without the original repository checkout.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent / "office_runtime"


def _run(cmd):
    print("+", " ".join(str(part) for part in cmd))
    subprocess.run(cmd, check=True)


def _verify_imports(python):
    verify = """
import importlib
mods = ["LibMTL", "torch", "torchvision", "PIL", "libmtl_office_benchmark"]
for name in mods:
    importlib.import_module(name)
print("office runtime imports: ok")
"""
    _run([python, "-c", verify])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install the bundled Office runtime package")
    parser.add_argument("--python", default=sys.executable, help="python executable to use")
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help="allow pip to resolve the package dependencies declared by the bundled runtime package",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        default=True,
        help="verify the resulting install by importing the bundled runtime package and its public deps",
    )
    parser.add_argument(
        "--no-verify",
        action="store_false",
        dest="verify",
        help="skip the import verification step",
    )
    args = parser.parse_args(argv)

    cmd = [args.python, "-m", "pip", "install", "-e", str(PACKAGE_ROOT)]
    if not args.with_deps:
        cmd.append("--no-deps")
    _run(cmd)
    print("office runtime package installed")
    print("runtime launch: python scripts/office_runtime/main.py --help")
    print("runtime launch after install: libmtl-office --help")

    if args.verify:
        _verify_imports(args.python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

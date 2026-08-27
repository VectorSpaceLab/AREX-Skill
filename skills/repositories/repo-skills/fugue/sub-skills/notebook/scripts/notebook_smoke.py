#!/usr/bin/env python3
"""Check Fugue notebook extension imports and optionally register magics in IPython."""
import argparse
import inspect
from typing import Sequence

from IPython import get_ipython

from fugue_notebook import NotebookSetup, setup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register Fugue notebook magics when running inside IPython.",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Pass fsql_ignore_case=True when registering.",
    )
    parser.add_argument(
        "--is-lab",
        action="store_true",
        help="Pass is_lab=True to avoid classic Notebook JavaScript injection.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"setup: {inspect.signature(setup)}")
    print(f"NotebookSetup: {inspect.signature(NotebookSetup)}")

    ip = get_ipython()
    if ip is None:
        print("IPython shell not detected; import check only.")
        return 0

    print("IPython shell detected.")
    if args.register:
        setup(is_lab=args.is_lab, fsql_ignore_case=args.ignore_case)
        print("fugue_notebook magics registered.")
    else:
        print("Use --register to register fugue_notebook magics in this shell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

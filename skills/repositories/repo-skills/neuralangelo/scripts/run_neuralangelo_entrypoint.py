#!/usr/bin/env python3
"""Run Neuralangelo project entry points through a bundled wrapper.

The wrapper keeps skill instructions anchored in this generated skill tree while
still executing the implementation from a user-provided Neuralangelo source tree.
It changes the working directory to --project-root, prepends it to sys.path, and
then delegates to the selected entry-point file with the remaining arguments.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import runpy
import shlex
import sys
from typing import Sequence

ENTRYPOINTS = {
    "train": Path("train.py"),
    "extract-mesh": Path("projects/neuralangelo/scripts/extract_mesh.py"),
    "generate-config": Path("projects/neuralangelo/scripts/generate_config.py"),
    "convert-data-to-json": Path("projects/neuralangelo/scripts/convert_data_to_json.py"),
    "convert-dtu-to-json": Path("projects/neuralangelo/scripts/convert_dtu_to_json.py"),
    "convert-tnt-to-json": Path("projects/neuralangelo/scripts/convert_tnt_to_json.py"),
}


def split_wrapper_args(argv: Sequence[str]) -> tuple[argparse.Namespace, list[str]]:
    if "--" in argv:
        idx = list(argv).index("--")
        wrapper_argv = list(argv[:idx])
        passthrough = list(argv[idx + 1 :])
    else:
        wrapper_argv = list(argv)
        passthrough = []
    parser = argparse.ArgumentParser(
        description="Delegate to a Neuralangelo project entry point from a bundled skill wrapper.",
        epilog="Place entry-point arguments after '--', for example: --entrypoint train -- --help",
    )
    parser.add_argument("--project-root", required=True, help="Target Neuralangelo source tree or project root.")
    parser.add_argument("--entrypoint", required=True, choices=sorted(ENTRYPOINTS), help="Entry point to run.")
    parser.add_argument("--print-only", action="store_true", help="Print the delegated command instead of executing it.")
    args = parser.parse_args(wrapper_argv)
    return args, passthrough


def shell_join(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def main(argv: Sequence[str] | None = None) -> int:
    args, passthrough = split_wrapper_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: --project-root is not a directory: {root}", file=sys.stderr)
        return 2
    entry_rel = ENTRYPOINTS[args.entrypoint]
    entry = root / entry_rel
    if not entry.is_file():
        print(f"error: selected entry point is missing under project root: {entry_rel}", file=sys.stderr)
        return 2

    delegated = [sys.executable, str(entry), *passthrough]
    if args.print_only:
        print(shell_join(delegated))
        return 0

    os.chdir(root)
    sys.path.insert(0, str(root))
    sys.argv = [str(entry), *passthrough]
    try:
        runpy.run_path(str(entry), run_name="__main__")
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        print(code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

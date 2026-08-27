#!/usr/bin/env python3
"""Build (do not run) a PyTracking LTR training command.

The script validates train_module/train_name by scanning ltr/train_settings in a
PyTracking checkout. It never imports training settings and never launches
training.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import sys
from typing import Dict, Iterable, List, Optional, Tuple


Pair = Tuple[str, str]


def _candidate_starts(script_path: pathlib.Path) -> Iterable[pathlib.Path]:
    yield pathlib.Path.cwd()
    yield script_path.parent
    for parent in script_path.parents:
        yield parent


def find_repo_root(repo_root: Optional[str]) -> pathlib.Path:
    """Find a checkout containing ltr/run_training.py and ltr/train_settings."""
    if repo_root:
        root = pathlib.Path(repo_root).expanduser().resolve()
        if not root.exists():
            raise SystemExit(f"--repo-root does not exist: {root}")
        return validate_repo_root(root)

    script_path = pathlib.Path(__file__).resolve()
    seen = set()
    for start in _candidate_starts(script_path):
        start = start.expanduser().resolve()
        for path in (start, *start.parents):
            if path in seen:
                continue
            seen.add(path)
            if (path / "ltr" / "run_training.py").is_file() and (path / "ltr" / "train_settings").is_dir():
                return path

    raise SystemExit(
        "Could not auto-detect a PyTracking checkout. Run from the checkout root "
        "or pass --repo-root PATH."
    )


def validate_repo_root(root: pathlib.Path) -> pathlib.Path:
    if not (root / "ltr" / "run_training.py").is_file():
        raise SystemExit(f"Missing ltr/run_training.py under repo root: {root}")
    if not (root / "ltr" / "train_settings").is_dir():
        raise SystemExit(f"Missing ltr/train_settings under repo root: {root}")
    return root


def scan_pairs(root: pathlib.Path) -> List[Pair]:
    settings_root = root / "ltr" / "train_settings"
    pairs: List[Pair] = []
    for module_dir in sorted(p for p in settings_root.iterdir() if p.is_dir()):
        if module_dir.name.startswith("__"):
            continue
        for file_path in sorted(module_dir.glob("*.py")):
            if file_path.name == "__init__.py" or file_path.name.startswith("."):
                continue
            pairs.append((module_dir.name, file_path.stem))
    return pairs


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def build_command(python_exe: str, module: str, name: str, no_cudnn_benchmark: bool) -> str:
    if no_cudnn_benchmark:
        code = (
            "from ltr.run_training import run_training; "
            f"run_training({module!r}, {name!r}, cudnn_benchmark=False)"
        )
        return shell_join([python_exe, "-c", code])
    return shell_join([python_exe, "ltr/run_training.py", module, name])


def format_list(pairs: List[Pair]) -> str:
    return "\n".join(f"{module}.{name}" for module, name in pairs)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a PyTracking LTR train_settings module/name pair and print "
            "a training command without launching training."
        )
    )
    parser.add_argument("train_module", nargs="?", help="Subdirectory under ltr/train_settings, e.g. dimp")
    parser.add_argument("train_name", nargs="?", help="Setting file stem, e.g. prdimp50")
    parser.add_argument(
        "--repo-root",
        help="Path to the PyTracking checkout. Defaults to auto-detecting from cwd or this script location.",
    )
    parser.add_argument("--python", default="python", help="Python executable to place in the emitted command.")
    parser.add_argument(
        "--no-cudnn-benchmark",
        action="store_true",
        help=(
            "Emit a Python API command with cudnn_benchmark=False. The source CLI's bool parser can treat "
            "text 'False' as true, so this option does not emit --cudnn_benchmark False."
        ),
    )
    parser.add_argument("--list", action="store_true", help="List available module/name pairs and exit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    root = find_repo_root(args.repo_root)
    pairs = scan_pairs(root)
    pair_set = set(pairs)

    if args.list:
        if args.json:
            print(json.dumps({"repo_root": str(root), "pairs": [f"{m}.{n}" for m, n in pairs]}, indent=2))
        else:
            print(format_list(pairs))
        return 0

    if not args.train_module or not args.train_name:
        available = format_list(pairs)
        raise SystemExit(
            "train_module and train_name are required unless --list is used.\n\n"
            f"Available pairs:\n{available}"
        )

    selected = (args.train_module, args.train_name)
    if selected not in pair_set:
        close = [f"{m}.{n}" for m, n in pairs if m == args.train_module or n == args.train_name]
        message = f"Unknown LTR training setting: {args.train_module}.{args.train_name}"
        if close:
            message += "\nNearby available pairs:\n" + "\n".join(close)
        else:
            message += "\nUse --list to see available pairs."
        raise SystemExit(message)

    command = build_command(args.python, args.train_module, args.train_name, args.no_cudnn_benchmark)
    result: Dict[str, object] = {
        "repo_root": str(root),
        "train_module": args.train_module,
        "train_name": args.train_name,
        "cudnn_benchmark": not args.no_cudnn_benchmark,
        "cwd": str(root),
        "command": command,
        "note": "Command was printed only; this helper does not launch training.",
    }
    if args.no_cudnn_benchmark:
        result["cudnn_note"] = (
            "Emitted Python API command because the source CLI parses bool strings unsafely."
        )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"# cwd: {root}")
        if args.no_cudnn_benchmark:
            print("# cudnn_benchmark: False via Python API call")
        print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

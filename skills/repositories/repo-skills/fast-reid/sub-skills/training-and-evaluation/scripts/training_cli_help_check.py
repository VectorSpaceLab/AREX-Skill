#!/usr/bin/env python3
"""Inspect FastReID's training CLI parser without launching training.

This helper is safe by default. It adds an explicit FastReID repository root to
sys.path, imports fastreid.engine.default_argument_parser, builds the parser,
and prints parser flags. It does not execute the source-tree launcher, call
launch(), train, evaluate, download, or write outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print FastReID training CLI flags without launching training.",
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to a FastReID repository/source root to add to sys.path.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print parser details as JSON instead of formatted help text.",
    )
    parser.add_argument(
        "--include-help",
        action="store_true",
        help="When using --json, also include the full argparse help text.",
    )
    return parser


def add_repo_root(repo_root: Path) -> None:
    resolved = repo_root.expanduser().resolve()
    if not resolved.is_dir():
        raise SystemExit(f"--repo-root is not a directory: {resolved}")
    if str(resolved) not in sys.path:
        sys.path.insert(0, str(resolved))


def safe_default(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def action_to_dict(action: argparse.Action) -> dict[str, Any]:
    return {
        "dest": action.dest,
        "option_strings": list(action.option_strings),
        "nargs": safe_default(action.nargs),
        "default": safe_default(action.default),
        "required": bool(getattr(action, "required", False)),
        "metavar": safe_default(action.metavar),
        "help": action.help,
    }


def import_training_parser() -> argparse.ArgumentParser:
    try:
        from fastreid.engine import default_argument_parser
    except ModuleNotFoundError as exc:
        missing = exc.name or "an imported dependency"
        raise SystemExit(
            "FastReID parser import failed because dependency "
            f"{missing!r} is missing. Install FastReID runtime dependencies "
            "or use the environment prepared for this checkout."
        ) from exc
    except ImportError as exc:
        message = str(exc)
        if "collections.Mapping" in message or "collections" in message:
            raise SystemExit(
                "FastReID parser import failed on a Python collections.Mapping "
                "compatibility issue. Use a Python version supported by this "
                "FastReID checkout or patch the legacy import before retrying."
            ) from exc
        raise SystemExit(f"FastReID parser import failed: {exc}") from exc

    return default_argument_parser()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    add_repo_root(args.repo_root)

    train_parser = import_training_parser()
    payload = {
        "status": "ok",
        "description": train_parser.description,
        "usage": train_parser.format_usage().strip(),
        "arguments": [action_to_dict(action) for action in train_parser._actions],
    }
    if args.include_help:
        payload["help"] = train_parser.format_help()

    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(train_parser.format_help())
        print("Detected flags:")
        for action in train_parser._actions:
            names = action.option_strings or [action.dest]
            print("- {}".format(", ".join(names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

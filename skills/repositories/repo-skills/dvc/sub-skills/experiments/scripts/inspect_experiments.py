#!/usr/bin/env python3
"""Print DVC experiment rows as JSON using the public dvc.api.exp_show API.

Safe defaults: this helper performs read-only local inspection and does not
contact network services unless the caller explicitly passes a remote/URL repo
value supported by DVC.

Examples:
    python inspect_experiments.py --repo .
    python inspect_experiments.py --repo . --rev HEAD --num 3 --param-deps --force
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect DVC experiments with dvc.api.exp_show and print JSON rows."
    )
    parser.add_argument(
        "--repo",
        default=None,
        help=(
            "DVC repository path to inspect. Defaults to the current project "
            "found by walking up from the current working directory."
        ),
    )
    parser.add_argument(
        "--rev",
        dest="revs",
        action="append",
        default=None,
        help="Git revision to use as an experiment baseline. Repeat for multiple revs.",
    )
    parser.add_argument(
        "--num",
        type=int,
        default=1,
        help=(
            "Number of first-parent commits to include from each baseline. "
            "Use a negative value for all first-parent commits."
        ),
    )
    parser.add_argument(
        "--param-deps",
        action="store_true",
        help="Show only parameters that are stage dependencies.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force DVC to re-collect experiment data instead of using cached rows.",
    )
    return parser


def _json_default(value: Any) -> str:
    return str(value)


def inspect_experiments(args: argparse.Namespace) -> list[dict[str, Any]]:
    try:
        from dvc.api import exp_show
    except ImportError as exc:
        raise RuntimeError(
            "Could not import dvc.api.exp_show. Install the dvc package in this Python environment."
        ) from exc

    revs: str | list[str] | None
    if args.revs is None:
        revs = None
    elif len(args.revs) == 1:
        revs = args.revs[0]
    else:
        revs = args.revs

    return exp_show(
        repo=args.repo,
        revs=revs,
        num=args.num,
        param_deps=args.param_deps,
        force=args.force,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rows = inspect_experiments(args)
    except Exception as exc:  # DVC raises several repo/config-specific exception types.
        message = str(exc) or exc.__class__.__name__
        hint = (
            "Run from inside a DVC repository or pass --repo <path>. "
            "This helper does not create a DVC project or configure remotes."
        )
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_type": exc.__class__.__name__,
                    "error": message,
                    "hint": hint,
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(json.dumps(rows, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

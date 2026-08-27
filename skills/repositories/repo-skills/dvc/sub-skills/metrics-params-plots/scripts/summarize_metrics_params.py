#!/usr/bin/env python3
"""Summarize DVC metrics and params via the public dvc.api helpers.

This helper is read-only: it imports dvc.api, calls metrics_show() and/or
params_show(), and prints a JSON result. It does not run pipeline stages, open
browsers, or read any files outside the repository paths passed to DVC.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def _json_default(value: Any) -> str:
    return repr(value)


def _string_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = os.fspath(value)
    return value if value else None


def _call_api(func, *targets: str, **kwargs: Any) -> dict[str, Any]:
    try:
        data = func(*targets, **kwargs)
    except Exception as exc:  # noqa: BLE001 - CLI helper must return JSON errors.
        return {
            "ok": False,
            "data": {},
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
    return {"ok": True, "data": data or {}}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a JSON summary from dvc.api.metrics_show() and "
            "dvc.api.params_show()."
        )
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="DVC repo path or URL. Defaults to the current project.",
    )
    parser.add_argument(
        "--rev",
        default=None,
        help="Git revision, branch, tag, commit, or experiment name to inspect.",
    )
    parser.add_argument(
        "--metrics-target",
        action="append",
        default=[],
        metavar="PATH",
        help="Metric file target to pass to dvc.api.metrics_show(); repeatable.",
    )
    parser.add_argument(
        "--params-target",
        action="append",
        default=[],
        metavar="PATH",
        help="Params file target to pass to dvc.api.params_show(); repeatable.",
    )
    parser.add_argument(
        "--stage",
        action="append",
        default=[],
        metavar="STAGE",
        help=(
            "Stage name for params_show(stages=...). Use "
            "subdir/dvc.yaml:stage for nested dvc.yaml files; repeatable."
        ),
    )
    parser.add_argument(
        "--deps",
        action="store_true",
        help="Limit params_show() to stage dependency params.",
    )
    parser.add_argument(
        "--skip-metrics",
        action="store_true",
        help="Do not call metrics_show().",
    )
    parser.add_argument(
        "--skip-params",
        action="store_true",
        help="Do not call params_show().",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation; use 0 for compact output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    warnings: list[str] = []

    try:
        import dvc.api as dvc_api
    except Exception as exc:  # noqa: BLE001 - report import failures as JSON.
        result = {
            "ok": False,
            "repo": _string_or_none(args.repo),
            "rev": _string_or_none(args.rev),
            "metrics": {"ok": False, "data": {}},
            "params": {"ok": False, "data": {}},
            "warnings": warnings,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
        print(json.dumps(result, indent=None if args.indent == 0 else args.indent))
        return 2

    repo = _string_or_none(args.repo)
    rev = _string_or_none(args.rev)
    common_kwargs = {"repo": repo, "rev": rev}

    if not args.metrics_target and not args.skip_metrics:
        warnings.append("No --metrics-target supplied; metrics_show() will use tracked metrics.")
    if not args.params_target and not args.skip_params:
        warnings.append("No --params-target supplied; params_show() will use tracked/default params.")

    metrics_result: dict[str, Any]
    if args.skip_metrics:
        metrics_result = {"ok": True, "skipped": True, "data": {}}
    else:
        metrics_result = _call_api(
            dvc_api.metrics_show,
            *args.metrics_target,
            **common_kwargs,
        )

    params_result: dict[str, Any]
    if args.skip_params:
        params_result = {"ok": True, "skipped": True, "data": {}}
    else:
        stages: str | list[str] | None
        if not args.stage:
            stages = None
        elif len(args.stage) == 1:
            stages = args.stage[0]
        else:
            stages = args.stage
        params_result = _call_api(
            dvc_api.params_show,
            *args.params_target,
            stages=stages,
            deps=args.deps,
            **common_kwargs,
        )

    ok = bool(metrics_result.get("ok")) and bool(params_result.get("ok"))
    result = {
        "ok": ok,
        "repo": repo,
        "rev": rev,
        "metrics_targets": args.metrics_target,
        "params_targets": args.params_target,
        "stages": args.stage,
        "deps": args.deps,
        "metrics": metrics_result,
        "params": params_result,
        "warnings": warnings,
    }
    print(
        json.dumps(
            result,
            indent=None if args.indent == 0 else args.indent,
            sort_keys=True,
            default=_json_default,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

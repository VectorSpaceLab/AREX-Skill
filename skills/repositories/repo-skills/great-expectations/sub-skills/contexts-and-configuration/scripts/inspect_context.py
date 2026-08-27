#!/usr/bin/env python3
"""Safely inspect Great Expectations import and Data Context basics.

The script uses only public GX APIs and prints a compact JSON summary without
printing absolute project roots, credentials, config-variable values, or Data
Docs URLs.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect Great Expectations import/version and create a safe "
            "ephemeral or optional file Data Context summary."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("ephemeral", "file"),
        default="ephemeral",
        help="Context mode to request. Defaults to ephemeral to avoid filesystem writes.",
    )
    parser.add_argument(
        "--project-root-dir",
        help=(
            "Optional project root for file mode. GX may scaffold a file context "
            "there if one does not already exist. The path is not printed."
        ),
    )
    parser.add_argument(
        "--context-root-dir",
        help=(
            "Optional context root for file mode, usually the directory containing "
            "great_expectations.yml. Do not combine with --project-root-dir."
        ),
    )
    parser.add_argument(
        "--show-signature",
        action="store_true",
        help="Include the public gx.get_context signature in the JSON output.",
    )
    return parser


def _public_methods(obj: Any, names: tuple[str, ...]) -> list[str]:
    return [name for name in names if hasattr(obj, name)]


def _manager_summary(context: Any) -> dict[str, dict[str, Any]]:
    expected_methods = ("add", "add_or_update", "get", "all", "delete")
    managers: dict[str, dict[str, Any]] = {}
    for attr in ("data_sources", "suites", "validation_definitions", "checkpoints"):
        try:
            manager = getattr(context, attr)
        except Exception as exc:  # noqa: BLE001 - diagnostics should not fail the whole script.
            managers[attr] = {"available": False, "error_type": type(exc).__name__}
            continue
        managers[attr] = {
            "available": True,
            "type": type(manager).__name__,
            "methods": _public_methods(manager, expected_methods),
        }
    return managers


def _store_summary(context: Any) -> dict[str, Any]:
    fields = (
        "expectations_store_name",
        "validation_results_store_name",
        "checkpoint_store_name",
    )
    summary: dict[str, Any] = {}
    for field in fields:
        try:
            summary[field] = getattr(context, field, None)
        except Exception as exc:  # noqa: BLE001
            summary[field] = {"error_type": type(exc).__name__}
    try:
        summary["store_names"] = sorted(getattr(context, "stores", {}).keys())
    except Exception as exc:  # noqa: BLE001
        summary["store_names"] = {"error_type": type(exc).__name__}
    try:
        data_docs_sites = getattr(context, "variables").config.data_docs_sites
        summary["data_docs_site_names"] = sorted((data_docs_sites or {}).keys())
    except Exception as exc:  # noqa: BLE001
        summary["data_docs_site_names"] = {"error_type": type(exc).__name__}
    return summary


def _context_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    if args.mode != "file":
        if args.project_root_dir or args.context_root_dir:
            raise ValueError("--project-root-dir and --context-root-dir are only valid with --mode file")
        return {"mode": "ephemeral"}

    if args.project_root_dir and args.context_root_dir:
        raise ValueError("Use either --project-root-dir or --context-root-dir, not both")

    kwargs: dict[str, Any] = {"mode": "file"}
    if args.project_root_dir:
        kwargs["project_root_dir"] = str(Path(args.project_root_dir))
    if args.context_root_dir:
        kwargs["context_root_dir"] = str(Path(args.context_root_dir))
    return kwargs


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        import great_expectations as gx
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "ok": False,
                    "stage": "import",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    summary: dict[str, Any] = {
        "ok": False,
        "great_expectations_imported": True,
        "great_expectations_version": getattr(gx, "__version__", "unknown"),
    }
    if args.show_signature:
        summary["get_context_signature"] = str(inspect.signature(gx.get_context))

    try:
        context = gx.get_context(**_context_kwargs(args))
    except Exception as exc:  # noqa: BLE001
        summary.update(
            {
                "stage": "get_context",
                "requested_mode": args.mode,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 2

    summary.update(
        {
            "ok": True,
            "requested_mode": args.mode,
            "context_type": type(context).__name__,
            "context_mode": getattr(context, "mode", None),
            "managers": _manager_summary(context),
            "stores": _store_summary(context),
        }
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

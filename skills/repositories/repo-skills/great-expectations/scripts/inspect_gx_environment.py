#!/usr/bin/env python3
"""Inspect the public Great Expectations Python API with safe local checks."""

from __future__ import annotations

import argparse
import inspect
import json
from typing import Any


def _json_default(value: Any) -> str:
    return repr(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Import Great Expectations, create an ephemeral Data Context, and print "
            "public API signals useful before using the Great Expectations skill."
        )
    )
    parser.add_argument(
        "--show-signatures",
        action="store_true",
        help="Include signatures for common top-level GX objects.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation to use for output.",
    )
    args = parser.parse_args()

    try:
        import great_expectations as gx
    except Exception as exc:  # pragma: no cover - used as user-facing diagnostic
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"Could not import great_expectations: {type(exc).__name__}: {exc}",
                    "next_step": "Install Great Expectations in this Python environment, then rerun the helper.",
                },
                indent=args.indent,
            )
        )
        return 1

    output: dict[str, Any] = {
        "ok": True,
        "version": getattr(gx, "__version__", None),
        "top_level_exports": list(getattr(gx, "__all__", [])),
    }

    try:
        context = gx.get_context(mode="ephemeral")
        output["context"] = {
            "type": type(context).__name__,
            "manager_types": {
                "data_sources": type(getattr(context, "data_sources", None)).__name__,
                "suites": type(getattr(context, "suites", None)).__name__,
                "validation_definitions": type(getattr(context, "validation_definitions", None)).__name__,
                "checkpoints": type(getattr(context, "checkpoints", None)).__name__,
            },
        }
        data_sources = context.data_sources
        factories = [
            name
            for name in dir(data_sources)
            if name.startswith("add_") or name.startswith("add_or_update_")
        ]
        output["datasource_factories_sample"] = sorted(factories)[:40]
        output["has_common_factories"] = {
            "add_pandas": hasattr(data_sources, "add_pandas"),
            "add_pandas_filesystem": hasattr(data_sources, "add_pandas_filesystem"),
            "add_sqlite": hasattr(data_sources, "add_sqlite"),
            "add_sql": hasattr(data_sources, "add_sql"),
            "add_spark": hasattr(data_sources, "add_spark"),
        }
    except Exception as exc:  # pragma: no cover - used as user-facing diagnostic
        output["ok"] = False
        output["context_error"] = f"{type(exc).__name__}: {exc}"
        output["next_step"] = "Read the contexts-and-configuration troubleshooting reference."

    if args.show_signatures:
        names = [
            "get_context",
            "ExpectationSuite",
            "ValidationDefinition",
            "Checkpoint",
            "ResultFormat",
        ]
        signatures: dict[str, str] = {}
        for name in names:
            value = getattr(gx, name, None)
            if value is None:
                signatures[name] = "<missing>"
                continue
            try:
                signatures[name] = str(inspect.signature(value))
            except Exception as exc:  # pragma: no cover - rare inspection failure
                signatures[name] = f"<signature unavailable: {type(exc).__name__}: {exc}>"
        output["signatures"] = signatures

    print(json.dumps(output, indent=args.indent, default=_json_default, sort_keys=True))
    return 0 if output.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

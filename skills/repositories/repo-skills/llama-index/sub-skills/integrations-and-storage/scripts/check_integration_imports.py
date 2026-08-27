#!/usr/bin/env python3
"""Check LlamaIndex integration distributions and import paths safely."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any


def check_distribution(name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": "distribution", "name": name}
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        result.update({"ok": False, "status": "missing"})
        return result

    requirements = list(dist.requires or [])
    result.update(
        {
            "ok": True,
            "status": "installed",
            "version": dist.version,
            "summary": dist.metadata.get("Summary"),
            "requires": requirements,
        }
    )
    return result


def check_module(name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"kind": "module", "name": name}
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should report all import failures.
        result.update(
            {
                "ok": False,
                "status": "import_failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        return result

    result.update(
        {
            "ok": True,
            "status": "imported",
            "file": getattr(module, "__file__", None),
            "package": getattr(module, "__package__", None),
        }
    )
    return result


def render_plain(results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in results:
        ok_marker = "OK" if item["ok"] else "FAIL"
        lines.append(f"[{ok_marker}] {item['kind']}: {item['name']} ({item['status']})")
        if item["kind"] == "distribution" and item["ok"]:
            lines.append(f"  version: {item.get('version')}")
            if item.get("summary"):
                lines.append(f"  summary: {item['summary']}")
            core_bounds = [req for req in item.get("requires", []) if req.startswith("llama-index-core")]
            if core_bounds:
                lines.append(f"  core requirement: {', '.join(core_bounds)}")
        elif item["kind"] == "module" and item["ok"]:
            if item.get("package"):
                lines.append(f"  package: {item['package']}")
            if item.get("file"):
                lines.append(f"  file: {item['file']}")
        elif not item["ok"]:
            if item.get("error_type"):
                lines.append(f"  error type: {item['error_type']}")
            if item.get("error"):
                lines.append(f"  error: {item['error']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely check installed LlamaIndex distributions and import paths. "
            "This reads local package metadata and imports requested modules only; "
            "it does not call provider APIs or open network connections."
        )
    )
    parser.add_argument(
        "--dist",
        action="append",
        default=[],
        metavar="NAME",
        help="Distribution/package name to check, e.g. llama-index-vector-stores-qdrant. Repeatable.",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        metavar="IMPORT_PATH",
        help="Python module import path to check, e.g. llama_index.vector_stores.qdrant. Repeatable.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of plain text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.dist and not args.module:
        parser.error("provide at least one --dist or --module")

    results = [check_distribution(name) for name in args.dist]
    results.extend(check_module(name) for name in args.module)

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print(render_plain(results))

    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

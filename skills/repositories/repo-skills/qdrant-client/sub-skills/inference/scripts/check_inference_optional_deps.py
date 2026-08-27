#!/usr/bin/env python3
"""Report qdrant-client inference optional dependency state without embedding data.

The script imports qdrant-client, checks package metadata, tries importing
FastEmbed, and lists supported model catalog counts/names when catalog APIs are
available. It does not instantiate embedding models and does not call embed,
query_embed, or passage_embed.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from typing import Any, Callable


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _safe_call(func: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = func()
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report failures.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "value": value}


def _catalog_summary(name: str, loader: Callable[[], Any], include_names: bool) -> dict[str, Any]:
    result = _safe_call(loader)
    summary: dict[str, Any] = {"catalog": name, "ok": result["ok"]}
    if not result["ok"]:
        summary["error"] = result["error"]
        return summary

    value = result["value"]
    if isinstance(value, dict):
        names = sorted(str(key) for key in value.keys())
        summary["count"] = len(names)
        if include_names:
            summary["models"] = names
        else:
            summary["sample"] = names[:10]
        return summary

    if isinstance(value, list):
        names = sorted(str(item.get("model", item)) if isinstance(item, dict) else str(item) for item in value)
        summary["count"] = len(names)
        if include_names:
            summary["models"] = names
        else:
            summary["sample"] = names[:10]
        return summary

    summary["type"] = type(value).__name__
    summary["repr"] = repr(value)
    return summary


def build_report(include_names: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "packages": {
            "qdrant-client": _distribution_version("qdrant-client"),
            "fastembed": _distribution_version("fastembed"),
            "fastembed-gpu": _distribution_version("fastembed-gpu"),
        },
    }

    qdrant_import = _safe_call(lambda: importlib.import_module("qdrant_client"))
    report["qdrant_client_import"] = {"ok": qdrant_import["ok"]}
    if not qdrant_import["ok"]:
        report["qdrant_client_import"]["error"] = qdrant_import["error"]
        return report

    client_import = _safe_call(lambda: importlib.import_module("qdrant_client.qdrant_client"))
    report["qdrant_client_module_import"] = {"ok": client_import["ok"]}
    if not client_import["ok"]:
        report["qdrant_client_module_import"]["error"] = client_import["error"]
        return report

    fastembed_import = _safe_call(lambda: importlib.import_module("fastembed"))
    report["fastembed_import"] = {"ok": fastembed_import["ok"]}
    if not fastembed_import["ok"]:
        report["fastembed_import"]["error"] = fastembed_import["error"]
        report["catalogs"] = []
        return report

    from qdrant_client import QdrantClient

    report["catalogs"] = [
        _catalog_summary("text", QdrantClient.list_text_models, include_names),
        _catalog_summary("image", QdrantClient.list_image_models, include_names),
        _catalog_summary(
            "late_interaction_text",
            QdrantClient.list_late_interaction_text_models,
            include_names,
        ),
        _catalog_summary(
            "late_interaction_multimodal",
            QdrantClient.list_late_interaction_multimodal_models,
            include_names,
        ),
        _catalog_summary("sparse", QdrantClient.list_sparse_models, include_names),
    ]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check qdrant-client inference optional dependencies without embedding data."
    )
    parser.add_argument(
        "--include-model-names",
        action="store_true",
        help="Print every model name from each available catalog instead of a short sample.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    report = build_report(include_names=args.include_model_names)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

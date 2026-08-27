#!/usr/bin/env python3
"""Safe LightRAG installed-package sanity check.

This script imports public LightRAG symbols, metadata, storage registry, and
console entry point metadata. It does not initialize storages, call models,
read credentials, start servers, connect to databases, or write data.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import sys
from typing import Any

EXPECTED_CONSOLE = {
    "lightrag-server",
    "lightrag-gunicorn",
    "lightrag-hash-password",
    "lightrag-download-cache",
    "lightrag-clean-llmqc",
    "lightrag-rebuild-vdb",
}
EXPECTED_STORAGE = {
    "JsonKVStorage",
    "NanoVectorDBStorage",
    "NetworkXStorage",
    "JsonDocStatusStorage",
}


def _version() -> str | None:
    for name in ("lightrag-hku", "lightrag"):
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return None


def _entry_points() -> dict[str, str]:
    try:
        eps = metadata.entry_points(group="console_scripts")
    except TypeError:
        eps = metadata.entry_points().get("console_scripts", [])
    return {ep.name: ep.value for ep in eps if ep.name.startswith("lightrag")}


def collect() -> dict[str, Any]:
    report: dict[str, Any] = {
        "distribution_version": _version(),
        "imports": {},
        "signatures": {},
        "storage_registry": {},
        "console_scripts": {},
        "missing": [],
    }
    try:
        lightrag = importlib.import_module("lightrag")
        report["imports"]["lightrag"] = "ok"
    except Exception as exc:
        report["imports"]["lightrag"] = repr(exc)
        report["missing"].append("lightrag import")
        return report

    for symbol in ("LightRAG", "QueryParam"):
        obj = getattr(lightrag, symbol, None)
        if obj is None:
            report["missing"].append(symbol)
        else:
            report["signatures"][symbol] = str(inspect.signature(obj))

    try:
        utils = importlib.import_module("lightrag.utils")
        for symbol in ("EmbeddingFunc", "wrap_embedding_func_with_attrs"):
            obj = getattr(utils, symbol, None)
            if obj is None:
                report["missing"].append(symbol)
            else:
                report["signatures"][symbol] = str(inspect.signature(obj))
    except Exception as exc:
        report["imports"]["lightrag.utils"] = repr(exc)
        report["missing"].append("lightrag.utils import")

    try:
        kg = importlib.import_module("lightrag.kg")
        storages = set(getattr(kg, "STORAGES", {}).keys())
        report["storage_registry"] = {
            "count": len(storages),
            "expected_local_present": sorted(EXPECTED_STORAGE & storages),
            "missing_expected_local": sorted(EXPECTED_STORAGE - storages),
        }
        if EXPECTED_STORAGE - storages:
            report["missing"].append("default storage registry entries")
    except Exception as exc:
        report["imports"]["lightrag.kg"] = repr(exc)
        report["missing"].append("lightrag.kg import")

    console = _entry_points()
    report["console_scripts"] = {
        "present": {name: console[name] for name in sorted(EXPECTED_CONSOLE & set(console))},
        "missing": sorted(EXPECTED_CONSOLE - set(console)),
    }
    report["ok"] = not report["missing"]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect installed LightRAG package symbols.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    parser.add_argument("--strict", action="store_true", help="exit non-zero if expected symbols are missing")
    args = parser.parse_args(argv)
    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "ok" if report.get("ok") else "issues"
        print(f"LightRAG install check: {status}")
        print(f"version: {report.get('distribution_version')}")
        print(f"missing: {', '.join(report.get('missing', [])) or 'none'}")
        print(f"console scripts: {', '.join(report.get('console_scripts', {}).get('present', {}).keys()) or 'none'}")
    return 1 if args.strict and not report.get("ok") else 0


if __name__ == "__main__":
    raise SystemExit(main())

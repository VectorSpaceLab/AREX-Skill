#!/usr/bin/env python3
"""Probe optional Hummingbird source-model dependencies without installing anything.

The script is intentionally read-only: it imports optional packages if present,
reports versions when available, and optionally inspects
``hummingbird.ml.supported`` to show which optional support lists/backends are
populated in the current Python process.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as metadata
import io
import json
import sys
import traceback
import warnings
from typing import Any, Dict, Iterable, List, Tuple

ProbeSpec = Tuple[str, str, str]

PROBES: List[ProbeSpec] = [
    ("lightgbm", "lightgbm", "LightGBM source models ([extra])"),
    ("xgboost", "xgboost", "XGBoost source models ([extra])"),
    ("prophet", "prophet", "Prophet source models ([extra])"),
    ("pyspark", "pyspark", "SparkML source models ([sparkml])"),
    ("pandas", "pandas", "pandas DataFrame inputs"),
    ("onnxruntime", "onnxruntime", "ONNX backend/runtime ([onnx])"),
    ("onnxmltools", "onnxmltools", "ONNX-ML tooling ([onnx])"),
    ("skl2onnx", "skl2onnx", "sklearn-to-ONNX tooling ([onnx])"),
    ("tvm", "tvm", "TVM backend (advanced optional)"),
]

SUPPORT_LISTS = [
    "lgbm_operator_list",
    "xgb_operator_list",
    "sparkml_operator_list",
    "prophet_operator_list",
    "onnxml_operator_list",
]


def _version_for(module: Any, dist_name: str) -> str | None:
    for candidate in (dist_name, dist_name.replace("_", "-"), dist_name.replace("-", "_")):
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            pass
    return getattr(module, "__version__", None)


def probe_import(import_name: str, dist_name: str, purpose: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "module": import_name,
        "purpose": purpose,
        "available": False,
        "version": None,
        "error_type": None,
        "error": None,
    }
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            module = importlib.import_module(import_name)
        result["available"] = True
        result["version"] = _version_for(module, dist_name)
        if caught:
            result["warnings"] = [str(w.message) for w in caught]
    except Exception as exc:  # import probes should not abort the report
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    return result


def _format_entry(entry: Any) -> str:
    if isinstance(entry, str):
        return entry
    name = getattr(entry, "__name__", None)
    module = getattr(entry, "__module__", None)
    if name and module:
        return f"{module}.{name}"
    if name:
        return name
    return repr(entry)


def _list_summary(value: Any, max_entries: int) -> Dict[str, Any]:
    if value is None:
        return {"populated": False, "count": 0, "sample": []}
    try:
        items = list(value)
    except TypeError:
        return {"populated": bool(value), "count": None, "sample": [repr(value)]}
    return {
        "populated": len(items) > 0,
        "count": len(items),
        "sample": [_format_entry(item) for item in items[:max_entries]],
    }


def collect_supported(max_entries: int = 8) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "imported": False,
        "error_type": None,
        "error": None,
        "captured_stdout": None,
        "warnings": [],
        "support_lists": {},
        "backends": {"populated": False, "aliases": [], "resolved": {}},
    }
    stream = io.StringIO()
    try:
        with warnings.catch_warnings(record=True) as caught, contextlib.redirect_stdout(stream):
            warnings.simplefilter("always")
            supported = importlib.import_module("hummingbird.ml.supported")
        result["imported"] = True
        result["warnings"] = [str(w.message) for w in caught]
        captured = stream.getvalue().strip()
        if captured:
            result["captured_stdout"] = captured

        for name in SUPPORT_LISTS:
            result["support_lists"][name] = _list_summary(getattr(supported, name, None), max_entries)

        raw_backends = getattr(supported, "backends", {})
        resolved: Dict[str, str] = {}
        try:
            for key, value in dict(raw_backends).items():
                if value is not None:
                    resolved[str(key)] = str(value)
        except Exception:
            resolved = {}
        result["backends"] = {
            "populated": bool(resolved),
            "aliases": sorted(resolved),
            "resolved": resolved,
        }
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        if sys.flags.dev_mode:
            result["traceback"] = traceback.format_exc()
        captured = stream.getvalue().strip()
        if captured:
            result["captured_stdout"] = captured
    return result


def build_report(include_supported: bool, max_entries: int) -> Dict[str, Any]:
    probes = [probe_import(import_name, dist_name, purpose) for import_name, dist_name, purpose in PROBES]
    report: Dict[str, Any] = {
        "schema_version": 1,
        "python": sys.version.split()[0],
        "imports": probes,
    }
    if include_supported:
        report["hummingbird_supported"] = collect_supported(max_entries=max_entries)
    return report


def _plain_table(rows: Iterable[Dict[str, Any]]) -> str:
    table_rows = []
    for row in rows:
        status = "yes" if row.get("available") else "no"
        version = row.get("version") or "-"
        note = row.get("purpose") or ""
        if not row.get("available") and row.get("error_type"):
            note = f"{note}; {row['error_type']}: {row.get('error') or ''}"
        table_rows.append([row.get("module", ""), status, version, note])
    headers = ["module", "available", "version", "purpose / note"]
    widths = [len(h) for h in headers]
    for row in table_rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], min(len(str(cell)), 100))

    def fmt(row: Iterable[Any]) -> str:
        return "  ".join(str(cell).ljust(widths[idx]) for idx, cell in enumerate(row))

    lines = [fmt(headers), fmt(["-" * w for w in widths])]
    lines.extend(fmt(row) for row in table_rows)
    return "\n".join(lines)


def print_text(report: Dict[str, Any]) -> None:
    print("Optional dependency imports")
    print(_plain_table(report["imports"]))
    supported = report.get("hummingbird_supported")
    if supported is None:
        return
    print("\nHummingbird supported registry")
    if not supported.get("imported"):
        print(f"not imported: {supported.get('error_type')}: {supported.get('error')}")
        return
    for name, summary in supported.get("support_lists", {}).items():
        populated = "yes" if summary.get("populated") else "no"
        print(f"{name}: populated={populated} count={summary.get('count')} sample={summary.get('sample')}")
    backends = supported.get("backends", {})
    print(f"backends: aliases={backends.get('aliases', [])}")
    if supported.get("warnings"):
        print(f"warnings: {supported['warnings']}")
    if supported.get("captured_stdout"):
        print(f"captured_stdout: {supported['captured_stdout']}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON instead of a text table")
    parser.add_argument(
        "--skip-supported",
        action="store_true",
        help="do not import hummingbird.ml.supported to inspect support lists/backends",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=8,
        help="maximum sample entries to show from each Hummingbird support list",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(include_supported=not args.skip_supported, max_entries=max(0, args.max_entries))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

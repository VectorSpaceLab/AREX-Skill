#!/usr/bin/env python3
"""Offline query helper for the bundled PINTO_model_zoo catalog.

The helper reads the generated JSON catalog and filters it locally. It never
imports ML runtimes or downloads artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[1] / "references" / "model-catalog.json"

FORMAT_ORDER = ("FP32", "FP16", "INT8", "DQ", "TPU", "WQ", "OV", "CM", "TFJS", "TF-TRT", "ONNX")
FORMAT_DISPLAY = {
    "FP32": "float32",
    "FP16": "float16",
    "INT8": "int8",
    "DQ": "dynamic range quantization",
    "TPU": "EdgeTPU",
    "WQ": "weight quantization",
    "OV": "OpenVINO",
    "CM": "CoreML",
    "TFJS": "TensorFlow.js",
    "TF-TRT": "TensorFlow-TensorRT",
    "ONNX": "ONNX",
}
FORMAT_ALIASES = {
    "fp32": "FP32",
    "float32": "FP32",
    "fp16": "FP16",
    "float16": "FP16",
    "int8": "INT8",
    "dq": "DQ",
    "dynamicrange": "DQ",
    "dynamicrangequantization": "DQ",
    "dynamicquantization": "DQ",
    "tpu": "TPU",
    "edgetpu": "TPU",
    "wq": "WQ",
    "weightquantization": "WQ",
    "weightquant": "WQ",
    "ov": "OV",
    "openvino": "OV",
    "coreml": "CM",
    "cm": "CM",
    "tfjs": "TFJS",
    "tensorflowjs": "TFJS",
    "tftrt": "TF-TRT",
    "tensorflowtensorrt": "TF-TRT",
    "onnx": "ONNX",
}


def _normalize_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


def _split_multi(values: list[str] | None) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        for part in str(raw).split(","):
            token = part.strip()
            if token and token not in seen:
                seen.add(token)
                tokens.append(token)
    return tokens


def _parse_numbers(values: list[str] | None) -> list[int]:
    numbers: list[int] = []
    seen: set[int] = set()
    for token in _split_multi(values):
        try:
            number = int(token)
        except ValueError as exc:
            raise SystemExit(f"Invalid catalog number: {token}") from exc
        if number not in seen:
            seen.add(number)
            numbers.append(number)
    return numbers


def _load_catalog(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise SystemExit(f"Invalid catalog schema in {path}")
    if data.get("schemaVersion") != 1:
        raise SystemExit(f"Unsupported catalog schema version in {path}")
    return data


def _canonical_format(value: str) -> str:
    key = _normalize_key(value)
    if not key:
        raise SystemExit("Empty format value")
    return FORMAT_ALIASES.get(key, value.strip().upper())


def _matches_any_field(value: Any, needles: list[str]) -> bool:
    if not needles:
        return True
    haystack = _normalize_text(value)
    return any(_normalize_text(needle) in haystack for needle in needles)


def _entry_blob(entry: dict[str, Any]) -> str:
    formats = [str(value) for value in entry.get("formats", []) if value is not None]
    parts = [
        str(entry.get("no", "")),
        str(entry.get("name", "")),
        str(entry.get("category", "")),
        str(entry.get("directory", "") or ""),
        str(entry.get("remarks", "") or ""),
    ]
    for flag in formats:
        parts.append(flag)
        parts.append(FORMAT_DISPLAY.get(flag, flag))
    return _normalize_text(" ".join(parts))


def _entry_matches(entry: dict[str, Any], args: argparse.Namespace) -> bool:
    categories = args.category or []
    names = args.name or []
    directories = args.directory or []
    numbers = args.number or []
    contains = args.contains or []
    formats = args.format or []

    if categories and not _matches_any_field(entry.get("category", ""), categories):
        return False
    if names and not _matches_any_field(entry.get("name", ""), names):
        return False
    directory = entry.get("directory")
    if directories:
        if directory is None or not _matches_any_field(directory, directories):
            return False
    if numbers:
        try:
            entry_no = int(entry.get("no"))
        except (TypeError, ValueError):
            return False
        if entry_no not in numbers:
            return False
    if formats:
        entry_formats = {str(value) for value in entry.get("formats", []) if value is not None}
        requested_formats = { _canonical_format(value) for value in formats }
        if not requested_formats.issubset(entry_formats):
            return False
    if contains:
        blob = _entry_blob(entry)
        if any(_normalize_text(term) not in blob for term in contains):
            return False
    return True


def _format_entry(entry: dict[str, Any]) -> str:
    directory = entry.get("directory") or "-"
    remarks = str(entry.get("remarks", "") or "-")
    formats = ",".join(str(value) for value in entry.get("formats", []) if value is not None)
    return f"{entry.get('no')} | {directory} | {entry.get('category', '')} | {formats} | {entry.get('name', '')} | {remarks}"


def _list_categories(catalog: dict[str, Any], json_mode: bool) -> int:
    counts = catalog.get("counts", {}).get("categories", {})
    items = sorted(counts.items(), key=lambda kv: (-int(kv[1]), kv[0].casefold()))
    if json_mode:
        payload = {"count": len(items), "categories": [{"category": name, "count": count} for name, count in items]}
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        for name, count in items:
            print(f"{count:>3}  {name}")
    return 0


def _list_formats(catalog: dict[str, Any], json_mode: bool) -> int:
    counts = catalog.get("counts", {}).get("formats", {})
    legend = catalog.get("format_legend", {})
    ordered_flags = [flag for flag in FORMAT_ORDER if flag in legend or flag in counts]
    extras = sorted(
        (set(legend) | set(counts)) - set(ordered_flags),
        key=str.casefold,
    )
    flags = ordered_flags + extras
    if json_mode:
        payload = {
            "count": len(flags),
            "formats": [
                {
                    "flag": flag,
                    "count": counts.get(flag, 0),
                    "meaning": legend.get(flag, FORMAT_DISPLAY.get(flag, flag)),
                }
                for flag in flags
            ],
        }
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        for flag in flags:
            meaning = legend.get(flag, FORMAT_DISPLAY.get(flag, flag))
            count = counts.get(flag, 0)
            print(f"{flag:<6} {count:>3}  {meaning}")
    return 0


def _print_matches(matches: list[dict[str, Any]], json_mode: bool, total_count: int) -> int:
    if json_mode:
        payload = {"count": total_count, "returned": len(matches), "matches": matches}
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return 0

    if not matches:
        print("No matching entries.")
        return 0

    if len(matches) < total_count:
        print(f"Showing {len(matches)} of {total_count} matches.")
    for entry in matches:
        print(_format_entry(entry))
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter the bundled PINTO_model_zoo catalog without network access.",
    )
    parser.add_argument("--category", action="append", help="Category filter; repeat or separate values with commas.")
    parser.add_argument("--format", action="append", help="Format filter; accepts catalog flags and aliases such as openvino, coreml, tfjs, tftrt, edgetpu, fp32, fp16, int8, dq, and wq.")
    parser.add_argument("--name", action="append", help="Model-name filter; repeat or separate values with commas.")
    parser.add_argument("--number", "--no", action="append", help="Catalog number filter; repeat or separate values with commas.")
    parser.add_argument("--directory", action="append", help="Folder-name filter; repeat or separate values with commas.")
    parser.add_argument("--contains", "--query", "-q", action="append", help="Broad substring search across catalog fields and remarks; repeat values to require all terms.")
    parser.add_argument("--limit", type=int, help="Limit the number of matched entries printed.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list-categories", action="store_true", help="List catalog categories and counts.")
    group.add_argument("--list-formats", action="store_true", help="List format flags, counts, and meanings.")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    args.category = _split_multi(args.category)
    args.format = _split_multi(args.format)
    args.name = _split_multi(args.name)
    args.number = _parse_numbers(args.number)
    args.directory = _split_multi(args.directory)
    args.contains = _split_multi(args.contains)

    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    catalog = _load_catalog(args.catalog)
    entries = [dict(entry) for entry in catalog["entries"]]
    entries.sort(key=lambda entry: (entry.get("no") is None, int(entry.get("no") or 10**9), str(entry.get("name", "")).casefold()))

    if args.list_categories:
        return _list_categories(catalog, args.json)
    if args.list_formats:
        return _list_formats(catalog, args.json)

    if args.limit is not None and args.limit < 0:
        raise SystemExit("--limit must be non-negative")

    matches = [entry for entry in entries if _entry_matches(entry, args)]
    total_count = len(matches)
    if args.limit is not None:
        matches = matches[: args.limit]
    return _print_matches(matches, args.json, total_count)


if __name__ == "__main__":
    raise SystemExit(main())

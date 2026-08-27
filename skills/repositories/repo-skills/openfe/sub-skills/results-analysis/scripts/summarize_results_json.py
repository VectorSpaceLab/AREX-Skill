#!/usr/bin/env python3
"""Summarize OpenFE result JSON files without running simulations or analysis."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

RESULT_SUFFIXES = (".json", ".json.gz")
TSV_FIELDS = [
    "path",
    "parse_status",
    "status",
    "result_like",
    "estimate",
    "estimate_value",
    "estimate_unit",
    "uncertainty",
    "uncertainty_value",
    "uncertainty_unit",
    "unit_result_count",
    "exception_count",
    "exception_sources",
    "protocol_data_keys",
    "inferred_legs",
    "notes",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read OpenFE result JSON or JSON.GZ files and summarize estimate, "
            "uncertainty, and status-like fields. This helper is read-only and "
            "does not run OpenFE analysis."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Result JSON files or directories to scan recursively.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "tsv"),
        default="json",
        help="Output format. Defaults to JSON.",
    )
    parser.add_argument(
        "--no-gufe-decoder",
        action="store_true",
        help="Use the standard JSON decoder even if gufe is installed.",
    )
    parser.add_argument(
        "--include-non-results",
        action="store_true",
        help="Include parseable JSON files that do not look like OpenFE result JSONs.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any selected file cannot be parsed or any input path is missing.",
    )
    return parser


def get_decoder(disable_gufe: bool) -> tuple[type[json.JSONDecoder] | None, str]:
    if disable_gufe:
        return None, "json"
    try:
        from gufe.tokenization import JSON_HANDLER  # type: ignore
    except Exception:
        return None, "json"
    return JSON_HANDLER.decoder, "gufe"


def is_result_suffix(path: Path) -> bool:
    path_text = path.name.lower()
    if path_text.endswith(RESULT_SUFFIXES):
        return True
    return path_text.endswith(".gz") and "json" in path_text


def collect_files(paths: Iterable[str]) -> tuple[list[Path], list[dict[str, Any]]]:
    files: list[Path] = []
    input_errors: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            input_errors.append(
                {
                    "path": str(path),
                    "parse_status": "missing_input",
                    "status": "error",
                    "result_like": False,
                    "notes": "Input path does not exist.",
                }
            )
            continue
        if path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file() and is_result_suffix(candidate))
        elif path.is_file():
            files.append(path)
    return sorted(set(files), key=lambda item: str(item)), input_errors


def open_text(path: Path):
    if path.name.lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def load_json_file(path: Path, decoder: type[json.JSONDecoder] | None) -> Any:
    with open_text(path) as handle:
        if decoder is None:
            return json.load(handle)
        return json.load(handle, cls=decoder)


def stringify(value: Any) -> str:
    if value is None:
        return ""
    try:
        return str(value)
    except Exception as exc:
        return f"<unprintable {type(value).__name__}: {exc}>"


def quantity_parts(value: Any) -> tuple[str, str, str]:
    if value is None:
        return "", "", ""

    magnitude = None
    unit = None
    for magnitude_attr in ("m", "magnitude"):
        if hasattr(value, magnitude_attr):
            try:
                magnitude = getattr(value, magnitude_attr)
                break
            except Exception:
                pass
    for unit_attr in ("u", "unit", "units"):
        if hasattr(value, unit_attr):
            try:
                unit = getattr(value, unit_attr)
                break
            except Exception:
                pass

    if magnitude is not None or unit is not None:
        return stringify(value), stringify(magnitude), stringify(unit)

    if isinstance(value, Mapping):
        possible_magnitude = first_present(value, ("m", "magnitude", "value"))
        possible_unit = first_present(value, ("u", "unit", "units"))
        if possible_magnitude is not None or possible_unit is not None:
            return stringify(value), stringify(possible_magnitude), stringify(possible_unit)

    if isinstance(value, (int, float, str)):
        return stringify(value), stringify(value), ""

    return stringify(value), "", ""


def first_present(mapping: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def flatten_mapping_values(value: Any, depth: int = 0) -> Iterable[Any]:
    if depth > 8:
        return
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from flatten_mapping_values(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from flatten_mapping_values(child, depth + 1)


def collect_protocol_data_keys(result: Mapping[str, Any]) -> list[str]:
    protocol_result = result.get("protocol_result")
    if not isinstance(protocol_result, Mapping):
        return []
    data = protocol_result.get("data")
    if isinstance(data, Mapping):
        return sorted(str(key) for key in data.keys())
    return []


def collect_inferred_legs(result: Mapping[str, Any]) -> list[str]:
    legs: set[str] = set()
    for mapping in flatten_mapping_values(result):
        if not isinstance(mapping, Mapping):
            continue
        simtype = mapping.get("simtype")
        if isinstance(simtype, str):
            legs.add(simtype)
        outputs = mapping.get("outputs")
        if isinstance(outputs, Mapping):
            output_simtype = outputs.get("simtype")
            if isinstance(output_simtype, str):
                legs.add(output_simtype)
    for key in collect_protocol_data_keys(result):
        if key in {"complex", "solvent", "vacuum", "overall"}:
            legs.add(key)
    return sorted(legs)


def summarize_unit_results(result: Mapping[str, Any]) -> tuple[int, int, list[str]]:
    unit_results = result.get("unit_results")
    if not isinstance(unit_results, Mapping):
        return 0, 0, []

    exception_sources: list[str] = []
    for key, unit_result in unit_results.items():
        if isinstance(unit_result, Mapping) and "exception" in unit_result:
            source = unit_result.get("source_key", key)
            exception_sources.append(str(source))
    return len(unit_results), len(exception_sources), sorted(exception_sources)


def result_like(data: Any) -> bool:
    return isinstance(data, Mapping) and bool(
        {"estimate", "uncertainty", "protocol_result", "unit_results"} & set(data.keys())
    )


def infer_status(result: Mapping[str, Any], unit_count: int, exception_count: int) -> tuple[str, list[str]]:
    notes: list[str] = []
    estimate_missing = "estimate" not in result or result.get("estimate") is None
    uncertainty_missing = "uncertainty" not in result or result.get("uncertainty") is None

    if estimate_missing:
        notes.append("missing estimate")
    if uncertainty_missing:
        notes.append("missing uncertainty")
    if "unit_results" in result and unit_count == 0:
        notes.append("empty unit_results")
    if unit_count and exception_count == unit_count:
        notes.append("all unit_results contain exceptions")
        return "failed", notes
    if exception_count:
        notes.append("some unit_results contain exceptions")
    if estimate_missing or uncertainty_missing:
        return "incomplete", notes
    return "success", notes


def summarize_data(path: Path, data: Any, decoder_name: str) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        return {
            "path": str(path),
            "parse_status": "parsed",
            "decoder": decoder_name,
            "status": "not_mapping",
            "result_like": False,
            "notes": "Top-level JSON value is not an object.",
        }

    unit_count, exception_count, exception_sources = summarize_unit_results(data)
    estimate, estimate_value, estimate_unit = quantity_parts(data.get("estimate"))
    uncertainty, uncertainty_value, uncertainty_unit = quantity_parts(data.get("uncertainty"))
    status, notes = infer_status(data, unit_count, exception_count)

    return {
        "path": str(path),
        "parse_status": "parsed",
        "decoder": decoder_name,
        "status": status,
        "result_like": result_like(data),
        "estimate": estimate,
        "estimate_value": estimate_value,
        "estimate_unit": estimate_unit,
        "uncertainty": uncertainty,
        "uncertainty_value": uncertainty_value,
        "uncertainty_unit": uncertainty_unit,
        "unit_result_count": unit_count,
        "exception_count": exception_count,
        "exception_sources": exception_sources,
        "protocol_data_keys": collect_protocol_data_keys(data),
        "inferred_legs": collect_inferred_legs(data),
        "notes": notes,
    }


def summarize_file(path: Path, decoder: type[json.JSONDecoder] | None, decoder_name: str) -> dict[str, Any]:
    try:
        data = load_json_file(path, decoder)
    except Exception as exc:
        return {
            "path": str(path),
            "parse_status": "parse_error",
            "decoder": decoder_name,
            "status": "error",
            "result_like": False,
            "notes": f"{type(exc).__name__}: {exc}",
        }
    return summarize_data(path, data, decoder_name)


def tsv_value(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def write_output(rows: list[dict[str, Any]], output_format: str) -> None:
    if output_format == "json":
        json.dump(rows, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return

    writer = csv.DictWriter(sys.stdout, fieldnames=TSV_FIELDS, delimiter="\t", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: tsv_value(row.get(field, "")) for field in TSV_FIELDS})


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    decoder, decoder_name = get_decoder(args.no_gufe_decoder)
    files, input_errors = collect_files(args.paths)

    rows = list(input_errors)
    for path in files:
        row = summarize_file(path, decoder, decoder_name)
        if args.include_non_results or row.get("result_like") or row.get("parse_status") != "parsed":
            rows.append(row)

    write_output(rows, args.format)

    if args.strict:
        has_errors = any(row.get("parse_status") in {"missing_input", "parse_error"} for row in rows)
        if has_errors:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

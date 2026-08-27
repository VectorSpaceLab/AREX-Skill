#!/usr/bin/env python3
"""Validate clearml-param-search JSON without importing ClearML or starting jobs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ALLOWED_SIGNS = {"min", "max", "min_global", "max_global"}
SEARCH_TYPES = {
    "UniformParameterRange": {
        "required": {"name", "type", "min_value", "max_value"},
        "optional": {"step_size", "include_max_value"},
        "numeric": {"min_value", "max_value", "step_size"},
        "integer": set(),
    },
    "UniformIntegerParameterRange": {
        "required": {"name", "type", "min_value", "max_value"},
        "optional": {"step_size", "include_max_value"},
        "numeric": set(),
        "integer": {"min_value", "max_value", "step_size"},
    },
    "LogUniformParameterRange": {
        "required": {"name", "type", "min_value", "max_value"},
        "optional": {"base", "step_size", "include_max_value"},
        "numeric": {"min_value", "max_value", "base", "step_size"},
        "integer": set(),
    },
    "DiscreteParameterRange": {
        "required": {"name", "type", "values"},
        "optional": set(),
        "numeric": set(),
        "integer": set(),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate JSON for clearml-param-search --params-search/--params-override "
            "without contacting ClearML. Values may be JSON strings or paths to JSON files."
        )
    )
    parser.add_argument(
        "--params-search",
        required=True,
        help="JSON object/list or path to JSON object/list for search ranges.",
    )
    parser.add_argument(
        "--params-override",
        help="Optional JSON object/list or path to JSON object/list for fixed overrides.",
    )
    parser.add_argument(
        "--objective-sign",
        required=True,
        help="Objective sign: min, max, min_global, or max_global.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON validation report instead of human-readable text.",
    )
    return parser.parse_args()


def read_json_or_path(value: str, label: str) -> Tuple[Any, List[str]]:
    warnings: List[str] = []
    path = Path(value)
    if path.is_file():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"{label}: failed reading {path}: {exc}") from exc
    else:
        text = value
        stripped = value.lstrip()
        if not stripped.startswith(("{", "[")):
            warnings.append(f"{label}: value is not an existing file path and does not look like JSON")
    try:
        return json.loads(text), warnings
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def as_object_list(value: Any, label: str) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if isinstance(value, dict):
        warnings.append(f"{label}: accepted a single object; files are easier to review as a JSON list")
        return [value], warnings, errors
    if not isinstance(value, list):
        return [], warnings, [f"{label}: expected a JSON object or list of objects"]
    objects: List[Dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}]: expected object, got {type(item).__name__}")
        else:
            objects.append(item)
    if not value:
        errors.append(f"{label}: expected at least one object")
    return objects, warnings, errors


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_name(item: Dict[str, Any], label: str) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    name = item.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{label}: 'name' must be a non-empty string")
    elif "/" not in name:
        warnings.append(f"{label}: CLI will prefix name without '/' as General/{name}")
    return errors, warnings


def validate_numeric_range(item: Dict[str, Any], label: str, integer: bool) -> List[str]:
    errors: List[str] = []
    min_value = item.get("min_value")
    max_value = item.get("max_value")
    if (integer and is_integer(min_value) and is_integer(max_value)) or (
        not integer and is_number(min_value) and is_number(max_value)
    ):
        if max_value < min_value:
            errors.append(f"{label}: max_value must be greater than or equal to min_value")
    return errors


def validate_step_size(item: Dict[str, Any], label: str, integer: bool) -> List[str]:
    if "step_size" not in item or item["step_size"] is None:
        return []
    value = item["step_size"]
    if integer:
        if not is_integer(value):
            return [f"{label}: step_size must be an integer"]
    elif not is_number(value):
        return [f"{label}: step_size must be a number"]
    if value <= 0:
        return [f"{label}: step_size must be greater than zero"]
    return []


def validate_search_item(item: Dict[str, Any], index: int) -> Tuple[List[str], List[str]]:
    label = f"params_search[{index}]"
    errors: List[str] = []
    warnings: List[str] = []
    name_errors, name_warnings = validate_name(item, label)
    errors.extend(name_errors)
    warnings.extend(name_warnings)

    param_type = item.get("type")
    if not isinstance(param_type, str):
        errors.append(f"{label}: 'type' must be a string")
        return errors, warnings
    if param_type not in SEARCH_TYPES:
        errors.append(f"{label}: unsupported type {param_type!r}; expected one of {sorted(SEARCH_TYPES)}")
        return errors, warnings

    spec = SEARCH_TYPES[param_type]
    required = spec["required"]
    allowed = required | spec["optional"]
    missing = sorted(key for key in required if key not in item)
    unknown = sorted(key for key in item if key not in allowed)
    if missing:
        errors.append(f"{label}: missing required field(s): {', '.join(missing)}")
    if unknown:
        errors.append(f"{label}: unknown field(s): {', '.join(unknown)}")

    for key in sorted(spec["numeric"]):
        if key in item and item[key] is not None and not is_number(item[key]):
            errors.append(f"{label}: {key} must be a number")
    for key in sorted(spec["integer"]):
        if key in item and item[key] is not None and not is_integer(item[key]):
            errors.append(f"{label}: {key} must be an integer")

    if "include_max_value" in item and not isinstance(item["include_max_value"], bool):
        errors.append(f"{label}: include_max_value must be true or false")

    if param_type == "DiscreteParameterRange":
        values = item.get("values")
        if not isinstance(values, list) or not values:
            errors.append(f"{label}: values must be a non-empty list")
    else:
        integer_range = param_type == "UniformIntegerParameterRange"
        errors.extend(validate_numeric_range(item, label, integer_range))
        errors.extend(validate_step_size(item, label, integer_range))
        if param_type == "LogUniformParameterRange" and "base" in item and item["base"] is not None:
            if is_number(item["base"]):
                if item["base"] <= 0:
                    errors.append(f"{label}: base must be greater than zero")
                elif item["base"] == 1:
                    warnings.append(f"{label}: base=1 produces no logarithmic scale")
    return errors, warnings


def validate_override_item(item: Dict[str, Any], index: int) -> Tuple[List[str], List[str]]:
    label = f"params_override[{index}]"
    errors: List[str] = []
    warnings: List[str] = []
    name_errors, name_warnings = validate_name(item, label)
    errors.extend(name_errors)
    warnings.extend(name_warnings)
    missing = sorted(key for key in ("name", "value") if key not in item)
    unknown = sorted(key for key in item if key not in {"name", "value"})
    if missing:
        errors.append(f"{label}: missing required field(s): {', '.join(missing)}")
    if unknown:
        errors.append(f"{label}: unknown field(s): {', '.join(unknown)}")
    return errors, warnings


def validate_all(params_search_raw: Any, params_override_raw: Optional[Any], objective_sign: str) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    if objective_sign not in ALLOWED_SIGNS:
        errors.append(
            "objective_sign: expected one of {}; got {!r}".format(
                ", ".join(sorted(ALLOWED_SIGNS)), objective_sign
            )
        )

    search_items, search_warnings, search_errors = as_object_list(params_search_raw, "params_search")
    warnings.extend(search_warnings)
    errors.extend(search_errors)
    for index, item in enumerate(search_items):
        item_errors, item_warnings = validate_search_item(item, index)
        errors.extend(item_errors)
        warnings.extend(item_warnings)

    override_items: List[Dict[str, Any]] = []
    if params_override_raw is not None:
        override_items, override_warnings, override_errors = as_object_list(params_override_raw, "params_override")
        warnings.extend(override_warnings)
        errors.extend(override_errors)
        for index, item in enumerate(override_items):
            item_errors, item_warnings = validate_override_item(item, index)
            errors.extend(item_errors)
            warnings.extend(item_warnings)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "params_search_count": len(search_items),
            "params_override_count": len(override_items),
            "objective_sign": objective_sign,
        },
    }


def print_text_report(report: Dict[str, Any]) -> None:
    if report["ok"]:
        print(
            "OK: validated {params_search_count} search parameter(s), "
            "{params_override_count} override(s), objective_sign={objective_sign}".format(**report["summary"])
        )
    else:
        print("Validation failed:", file=sys.stderr)
        for error in report["errors"]:
            print(f"- {error}", file=sys.stderr)
    if report["warnings"]:
        stream = sys.stdout if report["ok"] else sys.stderr
        print("Warnings:", file=stream)
        for warning in report["warnings"]:
            print(f"- {warning}", file=stream)


def main() -> int:
    args = parse_args()
    load_warnings: List[str] = []
    try:
        params_search_raw, warnings = read_json_or_path(args.params_search, "params_search")
        load_warnings.extend(warnings)
        params_override_raw = None
        if args.params_override is not None:
            params_override_raw, warnings = read_json_or_path(args.params_override, "params_override")
            load_warnings.extend(warnings)
    except ValueError as exc:
        report = {"ok": False, "errors": [str(exc)], "warnings": load_warnings, "summary": {}}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_text_report(report)
        return 1

    report = validate_all(params_search_raw, params_override_raw, args.objective_sign)
    report["warnings"] = load_warnings + report["warnings"]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

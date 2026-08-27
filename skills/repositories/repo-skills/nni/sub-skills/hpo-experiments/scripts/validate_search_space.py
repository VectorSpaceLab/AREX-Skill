#!/usr/bin/env python3
"""Validate common NNI HPO search-space JSON files.

This script is intentionally standalone: it does not import NNI and performs no
network, training, or destructive filesystem actions.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

TWO_VALUE_TYPES = {"randint", "uniform", "loguniform", "normal", "lognormal"}
THREE_VALUE_TYPES = {"quniform", "qloguniform", "qnormal", "qlognormal"}
COMMON_TYPES = {"choice", *TWO_VALUE_TYPES, *THREE_VALUE_TYPES}
LOG_BOUND_TYPES = {"loguniform", "qloguniform"}
SIGMA_TYPES = {"normal", "qnormal", "lognormal", "qlognormal"}
QUANTIZED_TYPES = {"quniform", "qloguniform", "qnormal", "qlognormal"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a JSON search-space file for common NNI HPO _type/_value shapes."
    )
    parser.add_argument("path", type=Path, help="Path to search_space.json")
    parser.add_argument(
        "--allow-unknown-types",
        action="store_true",
        help="Allow custom tuner-specific _type values after checking _type/_value presence.",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return nonzero when warnings are produced.",
    )
    return parser.parse_args()


def format_path(parts: list[str]) -> str:
    result = "$"
    for part in parts:
        if part.startswith("["):
            result += part
        elif part.isidentifier():
            result += "." + part
        else:
            result += "[" + json.dumps(part) + "]"
    return result


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_numeric_list(
    value: Any,
    expected_len: int,
    path: list[str],
    errors: list[str],
) -> list[float] | None:
    if not isinstance(value, list):
        errors.append(f"{format_path(path)}: _value must be a list of {expected_len} numbers")
        return None
    if len(value) != expected_len:
        errors.append(f"{format_path(path)}: _value must contain exactly {expected_len} numbers")
        return None
    if not all(is_number(item) for item in value):
        errors.append(f"{format_path(path)}: _value entries must be finite numbers")
        return None
    return [float(item) for item in value]


def validate_parameter_spec(
    spec: Any,
    path: list[str],
    errors: list[str],
    warnings: list[str],
    allow_unknown_types: bool,
) -> None:
    if not isinstance(spec, dict):
        errors.append(f"{format_path(path)}: parameter spec must be an object with _type and _value")
        return

    missing = [key for key in ("_type", "_value") if key not in spec]
    if missing:
        errors.append(f"{format_path(path)}: missing {', '.join(missing)}")
        for key, value in spec.items():
            if key not in {"_type", "_value", "_name"}:
                validate_nested(value, path + [key], errors, warnings, allow_unknown_types)
        return

    parameter_type = spec["_type"]
    value = spec["_value"]
    if not isinstance(parameter_type, str):
        errors.append(f"{format_path(path + ['_type'])}: _type must be a string")
        return

    if parameter_type not in COMMON_TYPES:
        message = f"{format_path(path + ['_type'])}: unknown common NNI search-space type {parameter_type!r}"
        if allow_unknown_types:
            warnings.append(message)
            validate_nested(value, path + ["_value"], errors, warnings, allow_unknown_types)
        else:
            errors.append(message)
        return

    if parameter_type == "choice":
        validate_choice(value, path + ["_value"], errors, warnings, allow_unknown_types)
        return

    expected_len = 2 if parameter_type in TWO_VALUE_TYPES else 3
    numeric_values = validate_numeric_list(value, expected_len, path + ["_value"], errors)
    if numeric_values is None:
        return

    if parameter_type == "randint":
        lower, upper = numeric_values
        if not float(lower).is_integer() or not float(upper).is_integer():
            errors.append(f"{format_path(path + ['_value'])}: randint bounds must be integers")
        if lower >= upper:
            errors.append(f"{format_path(path + ['_value'])}: randint lower bound must be less than upper bound")

    if parameter_type in {"uniform", "quniform", "loguniform", "qloguniform"}:
        lower, upper = numeric_values[0], numeric_values[1]
        if lower >= upper:
            errors.append(f"{format_path(path + ['_value'])}: lower bound must be less than upper bound")

    if parameter_type in LOG_BOUND_TYPES:
        lower, upper = numeric_values[0], numeric_values[1]
        if lower <= 0 or upper <= 0:
            errors.append(f"{format_path(path + ['_value'])}: loguniform bounds must be positive")

    if parameter_type in SIGMA_TYPES:
        sigma = numeric_values[1]
        if sigma <= 0:
            errors.append(f"{format_path(path + ['_value'])}: sigma must be positive")

    if parameter_type in QUANTIZED_TYPES:
        q = numeric_values[2]
        if q <= 0:
            errors.append(f"{format_path(path + ['_value'])}: quantization q must be positive")


def validate_choice(
    value: Any,
    path: list[str],
    errors: list[str],
    warnings: list[str],
    allow_unknown_types: bool,
) -> None:
    if not isinstance(value, list):
        errors.append(f"{format_path(path)}: choice _value must be a non-empty list")
        return
    if not value:
        errors.append(f"{format_path(path)}: choice _value must not be empty")
        return

    primitive_kinds = {type(item).__name__ for item in value if not isinstance(item, dict)}
    if len(primitive_kinds) > 1:
        warnings.append(f"{format_path(path)}: mixed primitive option types can be tuner-dependent")

    for index, option in enumerate(value):
        option_path = path + [f"[{index}]"]
        if isinstance(option, dict):
            if "_type" in option or "_value" in option:
                validate_parameter_spec(option, option_path, errors, warnings, allow_unknown_types)
            else:
                if "_name" not in option:
                    warnings.append(
                        f"{format_path(option_path)}: nested choice branch dict should include _name for built-in tuners"
                    )
                for key, nested_value in option.items():
                    if key != "_name":
                        validate_nested(nested_value, option_path + [key], errors, warnings, allow_unknown_types)
        elif isinstance(option, list):
            warnings.append(f"{format_path(option_path)}: list-valued choice options can be tuner-dependent")
        elif option is None:
            warnings.append(f"{format_path(option_path)}: null choice options can be tuner-dependent")
        elif isinstance(option, bool):
            warnings.append(f"{format_path(option_path)}: boolean choice options can be tuner-dependent")


def validate_nested(
    value: Any,
    path: list[str],
    errors: list[str],
    warnings: list[str],
    allow_unknown_types: bool,
) -> None:
    if isinstance(value, dict):
        if "_type" in value or "_value" in value:
            validate_parameter_spec(value, path, errors, warnings, allow_unknown_types)
        else:
            for key, nested_value in value.items():
                validate_nested(nested_value, path + [key], errors, warnings, allow_unknown_types)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_nested(item, path + [f"[{index}]"], errors, warnings, allow_unknown_types)


def validate_search_space(data: Any, allow_unknown_types: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return (["$: search space must be a top-level JSON object"], warnings)

    for name, spec in data.items():
        if not isinstance(name, str):
            errors.append("$: search-space parameter names must be strings")
            continue
        if name in {"_type", "_value"}:
            errors.append(f"{format_path([name])}: top-level search-space key looks like a parameter spec field")
            continue
        validate_parameter_spec(spec, [name], errors, warnings, allow_unknown_types)

    return errors, warnings


def main() -> int:
    args = parse_args()
    try:
        text = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2

    errors, warnings = validate_search_space(data, args.allow_unknown_types)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors or (warnings and args.warnings_as_errors):
        print(
            f"Search space invalid: {len(errors)} error(s), {len(warnings)} warning(s).",
            file=sys.stderr,
        )
        return 1

    print(f"Search space valid: {args.path} ({len(data)} top-level parameter(s), {len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

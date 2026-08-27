#!/usr/bin/env python3
"""Validate a GluonTS shell normal inference JSON payload.

The validator intentionally performs only local JSON/schema checks. It imports
installed gluonts for version visibility, but it does not start a server, build
Docker images, call AWS, train models, or read a source checkout.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import gluonts


VALID_OUTPUT_TYPES = {"mean", "samples", "quantiles"}


class ValidationError(Exception):
    """Raised for actionable payload validation failures."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a normal GluonTS shell /invocations payload: a JSON "
            "object with an instances list and optional configuration dict."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="JSON file to validate. If omitted, JSON is read from stdin.",
    )
    return parser.parse_args()


def load_json_payload(path: Path | None) -> Any:
    if path is None:
        text = sys.stdin.read()
        source = "stdin"
    else:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValidationError(f"cannot read --input file: {exc}") from exc
        source = str(path)

    if not text.strip():
        raise ValidationError(f"{source} is empty; provide a JSON payload")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def target_length(target: Any) -> int:
    if not isinstance(target, list):
        raise ValidationError("target must be a JSON list of numeric values or nested numeric lists")
    if len(target) == 0:
        raise ValidationError("target list must not be empty")

    if all(is_number(value) or value is None for value in target):
        return len(target)

    if all(isinstance(row, list) for row in target):
        row_lengths = []
        for row_idx, row in enumerate(target):
            if not row:
                raise ValidationError(f"target row {row_idx} is empty")
            if not all(is_number(value) or value is None for value in row):
                raise ValidationError(
                    f"target row {row_idx} must contain only numbers or nulls"
                )
            row_lengths.append(len(row))
        if len(set(row_lengths)) != 1:
            raise ValidationError("nested target rows must all have the same length")
        return row_lengths[0]

    raise ValidationError("target must be either a numeric list or a rectangular nested numeric list")


def validate_instance(instance: Any, index: int) -> int:
    if not isinstance(instance, dict):
        raise ValidationError(f"instances[{index}] must be a JSON object")

    missing = [field for field in ("start", "target") if field not in instance]
    if missing:
        raise ValidationError(
            f"instances[{index}] is missing required field(s): {', '.join(missing)}"
        )

    start = instance["start"]
    if not isinstance(start, str) or not start.strip():
        raise ValidationError(f"instances[{index}].start must be a non-empty string")

    try:
        return target_length(instance["target"])
    except ValidationError as exc:
        raise ValidationError(f"instances[{index}].{exc}") from exc


def positive_int_field(configuration: dict[str, Any], field: str) -> None:
    if field in configuration:
        value = configuration[field]
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValidationError(f"configuration.{field} must be a positive integer")


def validate_configuration(configuration: Any, warnings: list[str]) -> bool:
    if configuration is None:
        warnings.append(
            "configuration is absent; normal /invocations requests usually need configuration.freq, while batch mode can supply INFERENCE_CONFIG separately"
        )
        return False

    if not isinstance(configuration, dict):
        raise ValidationError("configuration must be a JSON object when provided")

    freq = configuration.get("freq")
    if freq is None:
        raise ValidationError("configuration.freq is required for normal shell /invocations requests")
    if not isinstance(freq, str) or not freq.strip():
        raise ValidationError("configuration.freq must be a non-empty string")

    for field in ("num_eval_samples", "num_samples"):
        positive_int_field(configuration, field)

    output_types = configuration.get("output_types")
    if output_types is not None:
        if not isinstance(output_types, list) or not output_types:
            raise ValidationError("configuration.output_types must be a non-empty list when provided")
        invalid = [value for value in output_types if value not in VALID_OUTPUT_TYPES]
        if invalid:
            raise ValidationError(
                "configuration.output_types contains unsupported value(s): "
                + ", ".join(map(str, invalid))
                + f"; expected one or more of {sorted(VALID_OUTPUT_TYPES)}"
            )

    quantiles = configuration.get("quantiles")
    if quantiles is not None:
        if not isinstance(quantiles, list):
            raise ValidationError("configuration.quantiles must be a list when provided")
        for idx, quantile in enumerate(quantiles):
            if not isinstance(quantile, (str, int, float)) or isinstance(quantile, bool):
                raise ValidationError(
                    f"configuration.quantiles[{idx}] must be a string or number"
                )
            try:
                q_value = float(quantile)
            except ValueError as exc:
                raise ValidationError(
                    f"configuration.quantiles[{idx}] must parse as a float between 0 and 1"
                ) from exc
            if not 0.0 <= q_value <= 1.0:
                raise ValidationError(
                    f"configuration.quantiles[{idx}] must be between 0 and 1"
                )

    return True


def validate_payload(payload: Any) -> tuple[int, list[int], bool, list[str]]:
    warnings: list[str] = []

    if not isinstance(payload, dict):
        raise ValidationError("top-level payload must be a JSON object")

    if "instances" not in payload:
        raise ValidationError("top-level payload is missing required field: instances")

    instances = payload["instances"]
    if not isinstance(instances, list):
        raise ValidationError("top-level instances field must be a JSON list")

    lengths = [validate_instance(instance, idx) for idx, instance in enumerate(instances)]

    configuration_present = validate_configuration(payload.get("configuration"), warnings)

    return len(instances), lengths, configuration_present, warnings


def main() -> int:
    args = parse_args()
    try:
        payload = load_json_payload(args.input)
        count, lengths, configuration_present, warnings = validate_payload(payload)
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    if lengths:
        length_summary = f"min_target_length={min(lengths)}, max_target_length={max(lengths)}"
    else:
        length_summary = "empty instances list"

    config_summary = "configuration=present" if configuration_present else "configuration=absent"
    print(
        f"OK: gluonts={gluonts.__version__}; instances={count}; {length_summary}; {config_summary}"
    )
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

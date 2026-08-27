#!/usr/bin/env python3
"""Safely validate the basic shape of a W&B sweep YAML/JSON config.

This script performs local structural checks only. It never imports wandb,
contacts W&B services, creates sweeps, or starts agents.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - environment-specific fallback
    yaml = None

ALLOWED_METHODS = {"grid", "random", "bayes", "custom"}
PARAMETER_KEYS = {
    "value",
    "values",
    "min",
    "max",
    "distribution",
    "probabilities",
    "mu",
    "sigma",
    "q",
    "parameters",
}
METRIC_GOALS = {"minimize", "maximize"}


class ValidationError(ValueError):
    """Raised when a sweep config fails local structural validation."""


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            inner = value[1:-1].strip()
            if not inner:
                return []
            return [parse_scalar(part) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def load_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        without_comment = raw_line.split("#", 1)[0].rstrip()
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        if "\t" in raw_line[:indent]:
            raise ValidationError(f"line {line_number}: tabs are not supported")
        stripped = without_comment.strip()
        if stripped.startswith("-"):
            raise ValidationError(
                f"line {line_number}: block lists require PyYAML; use inline lists like [a, b]"
            )
        if ":" not in stripped:
            raise ValidationError(f"line {line_number}: expected key: value")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise ValidationError(f"line {line_number}: empty key")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValidationError(f"line {line_number}: invalid indentation")
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def load_config(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if yaml is not None:
        return yaml.safe_load(text)
    return load_simple_yaml(text)


def validate_metric(config: dict[str, Any], errors: list[str]) -> None:
    metric = config.get("metric")
    if not isinstance(metric, dict):
        errors.append("metric must be a mapping with at least a name")
        return
    name = metric.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("metric.name must be a non-empty string")
    goal = metric.get("goal")
    if goal is not None and goal not in METRIC_GOALS:
        errors.append("metric.goal should be 'minimize' or 'maximize' when provided")


def validate_parameter(name: str, spec: Any, errors: list[str]) -> None:
    if not isinstance(spec, dict):
        errors.append(f"parameters.{name} must be a mapping")
        return
    if not spec:
        errors.append(f"parameters.{name} must not be empty")
        return
    if not PARAMETER_KEYS.intersection(spec):
        errors.append(
            f"parameters.{name} must include one of: "
            + ", ".join(sorted(PARAMETER_KEYS))
        )
    if "values" in spec:
        values = spec["values"]
        if not isinstance(values, list) or not values:
            errors.append(f"parameters.{name}.values must be a non-empty list")
    has_min = "min" in spec
    has_max = "max" in spec
    if has_min != has_max:
        errors.append(f"parameters.{name} should provide both min and max together")
    if has_min and has_max:
        try:
            if spec["min"] >= spec["max"]:
                errors.append(f"parameters.{name}.min must be less than max")
        except TypeError:
            errors.append(f"parameters.{name}.min and max must be comparable values")
    if "parameters" in spec:
        nested = spec["parameters"]
        if not isinstance(nested, dict) or not nested:
            errors.append(f"parameters.{name}.parameters must be a non-empty mapping")


def validate_parameters(config: dict[str, Any], errors: list[str]) -> None:
    parameters = config.get("parameters")
    if not isinstance(parameters, dict) or not parameters:
        errors.append("parameters must be a non-empty mapping")
        return
    for name, spec in parameters.items():
        if not isinstance(name, str) or not name.strip():
            errors.append("parameter names must be non-empty strings")
            continue
        validate_parameter(name, spec, errors)


def validate_config(config: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return ["sweep config must be a top-level mapping"]

    method = config.get("method")
    if not isinstance(method, str) or not method.strip():
        errors.append("method must be a non-empty string")
    elif method not in ALLOWED_METHODS:
        errors.append(
            "method is unusual; expected one of: " + ", ".join(sorted(ALLOWED_METHODS))
        )

    validate_metric(config, errors)
    validate_parameters(config, errors)

    program = config.get("program")
    has_function_hint = config.get("function") is not None
    if program is not None and (not isinstance(program, str) or not program.strip()):
        errors.append("program must be a non-empty string when provided")
    if program is None and not has_function_hint:
        errors.append(
            "no program is set; this is valid only when wandb.agent is called with a Python function"
        )

    if "count" in config:
        errors.append(
            "top-level count does not bound sweep execution; pass count to wandb.agent or --count to wandb agent"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the local structure of a W&B sweep YAML/JSON config."
    )
    parser.add_argument("config", type=Path, help="Path to a sweep .yaml, .yml, or .json file")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.config}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"ERROR: failed to load config: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # yaml parser exceptions vary by version
        print(f"ERROR: failed to parse config: {exc}", file=sys.stderr)
        return 2

    errors = validate_config(config)
    if errors:
        print("Sweep config failed local validation:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Sweep config passed local structural validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate a small, side-effect-free Mellea evaluation configuration.

The validator reads JSON or a deliberately small YAML subset. It never imports
Mellea, opens test files named by the config, starts a backend, invokes an LLM,
or executes generated code. It is a preflight check, not an evaluator.

Exit codes:
  0  configuration is valid
  2  input, parse, or schema error
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised for a malformed supported JSON/YAML configuration."""


def _strip_comment(line: str) -> str:
    """Remove an unquoted YAML comment and preserve quoted ``#`` characters."""
    quoted: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quoted == '"':
            escaped = True
            continue
        if char in ("'", '"'):
            if quoted == char:
                quoted = None
            elif quoted is None:
                quoted = char
        elif char == "#" and quoted is None and (
            index == 0 or line[index - 1].isspace()
        ):
            return line[:index].rstrip()
    return line.rstrip()


def _split_inline(value: str) -> list[str]:
    """Split a simple inline list while respecting quotes and brackets."""
    parts: list[str] = []
    start = 0
    depth = 0
    quoted: str | None = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quoted == '"':
            escaped = True
            continue
        if char in ("'", '"'):
            if quoted == char:
                quoted = None
            elif quoted is None:
                quoted = char
        elif quoted is None:
            if char in "[{(":
                depth += 1
            elif char in "]})":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(value[start:index].strip())
                start = index + 1
    parts.append(value[start:].strip())
    return parts


def _scalar(value: str) -> Any:
    """Parse a safe YAML scalar, with JSON and Python-literal conveniences."""
    value = value.strip()
    if not value:
        return None
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [_scalar(part) for part in _split_inline(value[1:-1]) if part]
    if value.startswith("{") and value.endswith("}"):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"invalid inline mapping: {value!r}") from exc
    if value[0:1] in {"'", '"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise ConfigError(f"invalid quoted scalar: {value!r}") from exc
        if not isinstance(parsed, (str, int, float, bool)) and parsed is not None:
            raise ConfigError(f"unsupported scalar: {value!r}")
        return parsed
    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", value):
        return float(value)
    return value


def _yaml_lines(text: str) -> list[tuple[int, str]]:
    """Return non-empty YAML lines as ``(indent, content)`` pairs."""
    result: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ConfigError(f"line {lineno}: tabs are not supported for indentation")
        content = _strip_comment(raw).strip()
        if not content:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        result.append((indent, content))
    return result


def _parse_yaml_node(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    """Parse one indentation-delimited mapping or scalar list."""
    if index >= len(lines) or lines[index][0] != indent:
        raise ConfigError("invalid indentation")
    is_list = lines[index][1] == "-" or lines[index][1].startswith("- ")
    container: dict[str, Any] | list[Any] = [] if is_list else {}

    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ConfigError(f"unexpected indentation near {content!r}")
        if is_list:
            if not (content == "-" or content.startswith("- ")):
                raise ConfigError(f"mixed mapping/list entries near {content!r}")
            item = content[1:].strip()
            index += 1
            if not item:
                if index >= len(lines) or lines[index][0] <= indent:
                    raise ConfigError("list item needs a value")
                child, index = _parse_yaml_node(lines, index, lines[index][0])
                container.append(child)
                continue
            # A list of scalar values is the supported common case. A simple
            # inline mapping is accepted as a convenience without constructors.
            if ":" in item and not item.startswith(("'", '"')):
                key, separator, raw_value = item.partition(":")
                if not separator or not key.strip():
                    raise ConfigError(f"invalid list mapping item: {item!r}")
                child_map: dict[str, Any] = {key.strip(): _scalar(raw_value)}
                if index < len(lines) and lines[index][0] > indent:
                    child, index = _parse_yaml_node(lines, index, lines[index][0])
                    if not isinstance(child, dict):
                        raise ConfigError("continued list mapping must be a mapping")
                    child_map.update(child)
                container.append(child_map)
            else:
                container.append(_scalar(item))
            continue

        if ":" not in content:
            raise ConfigError(f"mapping entry needs ':': {content!r}")
        key, _, raw_value = content.partition(":")
        key = key.strip()
        if not key:
            raise ConfigError("mapping key cannot be empty")
        index += 1
        if raw_value.strip():
            container[key] = _scalar(raw_value)
        else:
            if index >= len(lines) or lines[index][0] <= indent:
                container[key] = None
            else:
                child, index = _parse_yaml_node(lines, index, lines[index][0])
                container[key] = child
    return container, index


def parse_yaml_subset(text: str) -> Any:
    """Parse mappings and scalar lists from a safe, small YAML subset."""
    lines = _yaml_lines(text)
    if not lines:
        raise ConfigError("configuration is empty")
    value, index = _parse_yaml_node(lines, 0, lines[0][0])
    if index != len(lines):
        raise ConfigError("trailing or invalid YAML content")
    return value


def load_config(path: Path) -> tuple[Any, str]:
    """Read JSON first, then the supported YAML subset; never execute content."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text), "json"
    except json.JSONDecodeError:
        return parse_yaml_subset(text), "yaml"


def _nonempty_string(value: Any, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string")


def _positive_int(value: Any, field: str, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        errors.append(f"{field} must be a positive integer")


def validate_config(data: Any) -> tuple[dict[str, Any], list[str], list[str]]:
    """Return normalized config, errors, and non-fatal warnings."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {}, ["top-level configuration must be a mapping/object"], warnings

    required = ("backend", "test_files")
    for field in required:
        if field not in data:
            errors.append(f"missing required field: {field}")

    if "backend" in data:
        _nonempty_string(data["backend"], "backend", errors)
    if "test_files" in data:
        files = data["test_files"]
        if not isinstance(files, list) or not files:
            errors.append("test_files must be a non-empty list of strings")
        elif any(not isinstance(item, str) or not item.strip() for item in files):
            errors.append("test_files must contain only non-empty strings")

    for field in ("model", "judge_backend", "judge_model", "output_path"):
        if field in data:
            _nonempty_string(data[field], field, errors)
    if "output_format" in data and data["output_format"] not in {"json", "jsonl"}:
        errors.append("output_format must be 'json' or 'jsonl'")
    for field in ("max_gen_tokens", "max_judge_tokens"):
        if field in data:
            _positive_int(data[field], field, errors)
    if "continue_on_error" in data and not isinstance(data["continue_on_error"], bool):
        errors.append("continue_on_error must be a boolean")
    if "seed" in data and (
        isinstance(data["seed"], bool) or not isinstance(data["seed"], int)
    ):
        errors.append("seed must be an integer")

    threshold = data.get("threshold", 1.0)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        errors.append("threshold must be a finite number between 0 and 1")
    elif not math.isfinite(float(threshold)) or not 0 <= float(threshold) <= 1:
        errors.append("threshold must be a finite number between 0 and 1")
    elif float(threshold) != 1.0:
        warnings.append(
            "native m eval uses score == 1; a non-1 threshold requires post-processing"
        )

    known = {
        "backend", "model", "judge_backend", "judge_model", "test_files",
        "max_gen_tokens", "max_judge_tokens", "output_path", "output_format",
        "continue_on_error", "seed", "threshold",
    }
    unknown = sorted(set(data) - known)
    if unknown:
        warnings.append("unknown fields preserved: " + ", ".join(unknown))

    normalized = dict(data)
    normalized.setdefault("judge_backend", data.get("backend"))
    normalized.setdefault("output_format", "json")
    normalized.setdefault("threshold", 1.0)
    return normalized, errors, warnings


def main(argv: list[str] | None = None) -> int:
    """Validate one config and emit deterministic JSON diagnostics."""
    parser = argparse.ArgumentParser(
        description="Safely validate a small JSON/YAML Mellea evaluation config."
    )
    parser.add_argument("config", type=Path, help="JSON or supported YAML config path")
    args = parser.parse_args(argv)
    try:
        data, source_format = load_config(args.config)
        normalized, errors, warnings = validate_config(data)
    except ConfigError as exc:
        output = {"valid": False, "format": None, "normalized": {}, "errors": [str(exc)], "warnings": []}
        print(json.dumps(output, indent=2, sort_keys=True))
        return 2

    output = {
        "valid": not errors,
        "format": source_format,
        "normalized": normalized,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

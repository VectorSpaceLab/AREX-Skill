#!/usr/bin/env python3
"""Validate StarVLA LeRobot `meta/modality.json` without repo imports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_LANGUAGE_KEYS = (
    "human.task_description",
    "human.action.task_description",
    "language.language_instruction",
)


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")


def is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def require_object(value: Any, path: str, reporter: Reporter) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        reporter.error(path, "expected a JSON object")
        return None
    return value


def validate_top_level(doc: Any, reporter: Reporter) -> dict[str, Any] | None:
    obj = require_object(doc, "$", reporter)
    if obj is None:
        return None
    for key in ("video", "state", "action", "annotation"):
        if key not in obj:
            reporter.error(f"$.{key}", "missing required top-level object")
        elif not isinstance(obj[key], dict):
            reporter.error(f"$.{key}", "must be a JSON object")
        elif not obj[key]:
            reporter.error(f"$.{key}", "must not be empty")
    return obj


def validate_video(video: dict[str, Any], reporter: Reporter) -> None:
    for name, cfg in video.items():
        path = f"$.video.{name}"
        if not isinstance(name, str) or not name:
            reporter.error("$.video", "camera keys must be non-empty strings")
            continue
        if not isinstance(cfg, dict):
            reporter.error(path, "camera entry must be an object")
            continue
        original_key = cfg.get("original_key")
        if original_key is None:
            reporter.warn(path, "missing original_key; StarVLA will fall back to the camera key, which is rarely intended for custom datasets")
        elif not isinstance(original_key, str) or not original_key:
            reporter.error(f"{path}.original_key", "must be a non-empty string when provided")


def validate_state_action(modality: str, mapping: dict[str, Any], reporter: Reporter) -> None:
    seen_ranges: dict[str, list[tuple[int, int, str]]] = {}
    for name, cfg in mapping.items():
        path = f"$.{modality}.{name}"
        if not isinstance(name, str) or not name:
            reporter.error(f"$.{modality}", "field keys must be non-empty strings")
            continue
        if not isinstance(cfg, dict):
            reporter.error(path, "field entry must be an object")
            continue

        start = cfg.get("start")
        end = cfg.get("end")
        if not is_plain_int(start):
            reporter.error(f"{path}.start", "must be an integer")
            continue
        if not is_plain_int(end):
            reporter.error(f"{path}.end", "must be an integer")
            continue
        if start < 0:
            reporter.error(f"{path}.start", "must be non-negative")
        if end < 0:
            reporter.error(f"{path}.end", "must be non-negative")
        if end <= start:
            reporter.error(f"{path}", f"end must be greater than start; got start={start}, end={end}")

        original_key = cfg.get("original_key")
        if original_key is not None and (not isinstance(original_key, str) or not original_key):
            reporter.error(f"{path}.original_key", "must be a non-empty string when provided")
        column = original_key or ("observation.state" if modality == "state" else "action")
        if is_plain_int(start) and is_plain_int(end):
            seen_ranges.setdefault(column, []).append((start, end, name))

        rotation_type = cfg.get("rotation_type")
        if rotation_type is not None and not isinstance(rotation_type, str):
            reporter.error(f"{path}.rotation_type", "must be a string when provided")
        absolute = cfg.get("absolute")
        if absolute is not None and not isinstance(absolute, bool):
            reporter.error(f"{path}.absolute", "must be a boolean when provided")
        dtype = cfg.get("dtype")
        if dtype is not None and not isinstance(dtype, str):
            reporter.error(f"{path}.dtype", "must be a string when provided")

    for column, ranges in seen_ranges.items():
        ranges = sorted(ranges)
        for (prev_start, prev_end, prev_name), (start, end, name) in zip(ranges, ranges[1:]):
            if start < prev_end:
                reporter.warn(
                    f"$.{modality}.{name}",
                    f"slice {start}:{end} overlaps {prev_name} {prev_start}:{prev_end} in original_key {column!r}; this can be valid only if intentional",
                )


def validate_annotation(annotation: dict[str, Any], language_key: str | None, reporter: Reporter) -> None:
    flat_fields: dict[str, dict[str, Any]] = {}
    nested_candidates: list[str] = []

    for key, value in annotation.items():
        path = f"$.annotation.{key}"
        if not isinstance(key, str) or not key:
            reporter.error("$.annotation", "annotation keys must be non-empty strings")
            continue
        if not isinstance(value, dict):
            reporter.error(path, "annotation entry must be an object")
            continue
        if "original_key" in value:
            flat_fields[key] = value
        else:
            nested_candidates.append(key)
            reporter.error(
                path,
                "nested annotation objects are not accepted by StarVLA's current parser; use a flat key such as "
                f"{key}.task_description with {'{'}\"original_key\": \"task_index\"{'}'} if that matches your DataConfig language key",
            )

    if language_key:
        expected = [language_key.removeprefix("annotation.")]
    else:
        expected = list(DEFAULT_LANGUAGE_KEYS)

    present = [key for key in expected if key in flat_fields]
    if not present:
        expected_text = ", ".join(f"annotation.{key}" for key in expected)
        reporter.error(
            "$.annotation",
            f"missing language annotation key; expected one of: {expected_text}. "
            "Pass --language-key if the DataConfig uses a different annotation subkey.",
        )
        if nested_candidates:
            reporter.warn(
                "$.annotation",
                "nested annotation entries were found, but StarVLA looks up flat subkeys after removing the 'annotation.' prefix from DataConfig.language_keys",
            )
        return

    for key in present:
        field = flat_fields[key]
        original_key = field.get("original_key")
        if original_key != "task_index":
            reporter.error(
                f"$.annotation.{key}.original_key",
                f"must be 'task_index' for StarVLA language lookup; got {original_key!r}",
            )

    for key, field in flat_fields.items():
        original_key = field.get("original_key")
        if original_key is not None and not isinstance(original_key, str):
            reporter.error(f"$.annotation.{key}.original_key", "must be a string when provided")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a StarVLA LeRobot meta/modality.json file. "
            "Checks top-level video/state/action/annotation, state/action integer slices, "
            "and language original_key == task_index."
        )
    )
    parser.add_argument("path", type=Path, help="Path to meta/modality.json")
    parser.add_argument(
        "--language-key",
        default=None,
        help=(
            "Expected DataConfig language key or annotation subkey. "
            "Examples: annotation.human.task_description, human.action.task_description. "
            "If omitted, accepts common StarVLA language keys."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors and warnings; suppress the final OK line.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    reporter = Reporter()

    try:
        with args.path.open("r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except FileNotFoundError:
        print(f"ERROR: {args.path}: file not found", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: {args.path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: {args.path}: unable to read file: {exc}", file=sys.stderr)
        return 2

    obj = validate_top_level(doc, reporter)
    if obj is not None:
        if isinstance(obj.get("video"), dict):
            validate_video(obj["video"], reporter)
        if isinstance(obj.get("state"), dict):
            validate_state_action("state", obj["state"], reporter)
        if isinstance(obj.get("action"), dict):
            validate_state_action("action", obj["action"], reporter)
        if isinstance(obj.get("annotation"), dict):
            validate_annotation(obj["annotation"], args.language_key, reporter)

    for warning in reporter.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in reporter.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if reporter.errors:
        print(
            f"FAILED: {args.path} has {len(reporter.errors)} error(s) and {len(reporter.warnings)} warning(s).",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(f"OK: {args.path} passed StarVLA modality.json checks ({len(reporter.warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

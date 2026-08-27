#!/usr/bin/env python3
"""Self-contained feature schema smoke checks for Hugging Face Datasets.

The script builds tiny in-memory examples and validates that Datasets accepts or
rejects them under explicit Features. It avoids network access, media decoding,
and repository-local files.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def _import_datasets():
    try:
        from datasets import ClassLabel, Dataset, Features, Json, List, Value
    except Exception as exc:  # pragma: no cover - message is for user environments
        raise SystemExit(
            "Could not import the 'datasets' package. Install Hugging Face Datasets "
            "in the active Python environment before running this smoke check. "
            f"Original error: {exc}"
        ) from exc
    return ClassLabel, Dataset, Features, Json, List, Value


def _object_detection_case(bad_example: bool) -> tuple[Any, dict[str, list[Any]]]:
    ClassLabel, _Dataset, Features, _Json, List, Value = _import_datasets()
    features = Features(
        {
            "image": Value("string"),
            "objects": List(
                {
                    "bbox": List(Value("float32"), length=4),
                    "category": ClassLabel(names=["cat", "dog"]),
                }
            ),
        }
    )
    if bad_example:
        data = {
            "image": ["image-1.jpg"],
            "objects": [[{"bbox": [0.0, 1.0, 2.0], "category": "cat"}]],
        }
    else:
        data = {
            "image": ["image-1.jpg"],
            "objects": [[{"bbox": [0.0, 1.0, 2.0, 3.0], "category": "cat"}]],
        }
    return features, data


def _messages_case(bad_example: bool) -> tuple[Any, dict[str, list[Any]]]:
    _ClassLabel, _Dataset, Features, Json, List, Value = _import_datasets()
    features = Features(
        {
            "messages": List(
                {
                    "role": Value("string"),
                    "content": Value("string"),
                    "tool_calls": List(Json()),
                }
            )
        }
    )
    if bad_example:
        data = {
            "messages": [
                [
                    {"role": "user", "content": "hello", "tool_calls": []},
                    {"role": "assistant", "content": {"not": "a string"}, "tool_calls": []},
                ]
            ]
        }
    else:
        data = {
            "messages": [
                [
                    {"role": "user", "content": "hello", "tool_calls": []},
                    {"role": "assistant", "content": "hi", "tool_calls": [{"name": "search", "args": {"q": "x"}}]},
                ]
            ]
        }
    return features, data


def _preflight_object_detection(data: dict[str, list[Any]]) -> None:
    for row_index, objects in enumerate(data["objects"]):
        for object_index, obj in enumerate(objects):
            bbox = obj.get("bbox")
            if not isinstance(bbox, list) or len(bbox) != 4:
                raise ValueError(f"objects[{row_index}][{object_index}].bbox must contain exactly 4 coordinates")
            category = obj.get("category")
            if category not in {"cat", "dog", 0, 1}:
                raise ValueError(f"objects[{row_index}][{object_index}].category is not in the declared ClassLabel names")


def _preflight_messages(data: dict[str, list[Any]]) -> None:
    for row_index, messages in enumerate(data["messages"]):
        for message_index, message in enumerate(messages):
            content = message.get("content")
            if not isinstance(content, str):
                raise ValueError(f"messages[{row_index}][{message_index}].content must be a string")
            tool_calls = message.get("tool_calls")
            if not isinstance(tool_calls, list):
                raise ValueError(f"messages[{row_index}][{message_index}].tool_calls must be a list")


def run_case(case: str, bad_example: bool) -> int:
    _ClassLabel, Dataset, _Features, _Json, _List, _Value = _import_datasets()
    builders = {
        "object-detection": _object_detection_case,
        "messages": _messages_case,
    }
    preflight = {
        "object-detection": _preflight_object_detection,
        "messages": _preflight_messages,
    }
    features, data = builders[case](bad_example)
    expected_failure = bad_example
    try:
        preflight[case](data)
        dataset = Dataset.from_dict(data, features=features)
    except Exception as exc:
        if expected_failure:
            print(f"PASS: {case} bad example was rejected: {type(exc).__name__}: {exc}")
            return 0
        print(f"FAIL: {case} valid example was rejected: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if expected_failure:
        print(f"FAIL: {case} bad example was accepted unexpectedly", file=sys.stderr)
        print(f"Inferred/declared features: {dataset.features}", file=sys.stderr)
        return 1

    print(f"PASS: {case} valid example accepted")
    print(f"Rows: {dataset.num_rows}")
    print(f"Features: {dataset.features}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny in-memory Hugging Face Datasets feature schema smoke checks."
    )
    parser.add_argument(
        "--case",
        choices=["object-detection", "messages"],
        default="object-detection",
        help="Schema example to validate. Defaults to object-detection.",
    )
    parser.add_argument(
        "--bad-example",
        action="store_true",
        help="Use an intentionally invalid example and pass only if Datasets rejects it.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run_case(args.case, args.bad_example)


if __name__ == "__main__":
    raise SystemExit(main())

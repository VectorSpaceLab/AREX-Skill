from __future__ import annotations

import json
from typing import Any


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_items(items: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    normalized = []
    for item in items or []:
        normalized.append({
            "input": _clean(item.get("input")),
            "output": _clean(item.get("output")),
            "reason": _clean(item.get("reason")),
        })
    return normalized


def build_instruction_record(task_id: str, dataset: str, category: str, definition: str = "", prompt: str = "", things_to_avoid: str = "", emphasis: str = "", positive_examples: list[dict[str, Any]] | None = None, negative_examples: list[dict[str, Any]] | None = None, instances: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    record = {
        "task_id": _clean(task_id),
        "dataset": _clean(dataset),
        "category": _clean(category),
        "definition": _clean(definition),
        "prompt": _clean(prompt),
        "things_to_avoid": _clean(things_to_avoid),
        "emphasis": _clean(emphasis),
        "positive_examples": _normalize_items(positive_examples),
        "negative_examples": _normalize_items(negative_examples),
        "instances": _normalize_items(instances),
    }
    validate_instruction_record(record)
    return record


def validate_instruction_record(record: dict[str, Any]) -> None:
    for field in ["task_id", "dataset", "category"]:
        if not _clean(record.get(field)):
            raise ValueError(f"missing required field: {field}")
    if not (_clean(record.get("definition")) or _clean(record.get("prompt"))):
        raise ValueError("instruction must include definition or prompt")
    instances = record.get("instances")
    if not isinstance(instances, list) or not instances:
        raise ValueError("instruction must include at least one instance")
    for idx, item in enumerate(instances):
        if not _clean(item.get("input")) or not _clean(item.get("output")):
            raise ValueError(f"instance {idx} must include input and output")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.load(open(args.input_json, encoding="utf-8"))
    record = build_instruction_record(**payload)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)


if __name__ == "__main__":
    main()

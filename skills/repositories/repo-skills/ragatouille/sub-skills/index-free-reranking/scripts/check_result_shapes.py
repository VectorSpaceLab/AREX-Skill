#!/usr/bin/env python3
"""Validate RAGatouille index-free result-shape JSON without loading models."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {"content", "score", "rank", "result_index"}


class ValidationError(Exception):
    """Raised when a result payload does not match the expected shape."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate sample JSON shaped like RAGPretrainedModel.rerank() or "
            "search_encoded_docs() results. This script does not import "
            "RAGatouille, load models, download checkpoints, or use GPUs."
        )
    )
    parser.add_argument(
        "json_path",
        nargs="?",
        help="Path to a JSON file. Omit or use '-' to read JSON from stdin.",
    )
    parser.add_argument(
        "--mode",
        choices=("rerank", "encoded-search"),
        default="rerank",
        help="Result family to validate. Both share core keys; encoded-search may include metadata.",
    )
    parser.add_argument(
        "--require-metadata",
        action="store_true",
        help="Require document_metadata on every result item, useful for metadata-bearing encoded-search samples.",
    )
    parser.add_argument(
        "--expect-nested",
        choices=("auto", "flat", "nested"),
        default="auto",
        help="Validate flat single-query or nested multi-query result shape.",
    )
    parser.add_argument(
        "--max-rank-start",
        type=int,
        default=None,
        help="Optional maximum acceptable first rank value for each result list, e.g. 0 or 1.",
    )
    return parser.parse_args()


def load_payload(path: str | None) -> Any:
    if path in (None, "-"):
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_item(item: Any, path: str, require_metadata: bool) -> None:
    if not isinstance(item, dict):
        raise ValidationError(f"{path} must be an object, got {type(item).__name__}")

    missing = REQUIRED_KEYS.difference(item)
    if missing:
        raise ValidationError(f"{path} missing required keys: {', '.join(sorted(missing))}")

    if not isinstance(item["content"], str):
        raise ValidationError(f"{path}.content must be a string")
    if not is_number(item["score"]):
        raise ValidationError(f"{path}.score must be a number")
    if not isinstance(item["rank"], int) or isinstance(item["rank"], bool):
        raise ValidationError(f"{path}.rank must be an integer")
    if not isinstance(item["result_index"], int) or isinstance(item["result_index"], bool):
        raise ValidationError(f"{path}.result_index must be an integer")
    if item["result_index"] < 0:
        raise ValidationError(f"{path}.result_index must be non-negative")

    if "document_metadata" in item and item["document_metadata"] is not None:
        if not isinstance(item["document_metadata"], dict):
            raise ValidationError(f"{path}.document_metadata must be an object or null")
    elif require_metadata:
        raise ValidationError(f"{path} missing required document_metadata")


def validate_result_list(
    items: Any,
    path: str,
    require_metadata: bool,
    max_rank_start: int | None,
) -> int:
    if not isinstance(items, list):
        raise ValidationError(f"{path} must be a list")
    if not items:
        return 0

    for index, item in enumerate(items):
        validate_item(item, f"{path}[{index}]", require_metadata)

    if max_rank_start is not None and items[0]["rank"] > max_rank_start:
        raise ValidationError(
            f"{path}[0].rank is {items[0]['rank']}, expected <= {max_rank_start}"
        )
    return len(items)


def detect_shape(payload: Any) -> str:
    if not isinstance(payload, list):
        raise ValidationError(f"top-level JSON must be a list, got {type(payload).__name__}")
    if not payload:
        return "flat"
    if all(isinstance(item, dict) for item in payload):
        return "flat"
    if all(isinstance(item, list) for item in payload):
        return "nested"
    raise ValidationError("top-level list must contain only result objects or only per-query lists")


def validate_payload(args: argparse.Namespace, payload: Any) -> dict[str, Any]:
    shape = detect_shape(payload)
    if args.expect_nested == "flat" and shape != "flat":
        raise ValidationError("expected a flat single-query result list")
    if args.expect_nested == "nested" and shape != "nested":
        raise ValidationError("expected a nested multi-query result list")

    total_results = 0
    query_count = 1
    if shape == "flat":
        total_results = validate_result_list(
            payload,
            "$",
            require_metadata=args.require_metadata,
            max_rank_start=args.max_rank_start,
        )
    else:
        query_count = len(payload)
        for query_index, items in enumerate(payload):
            total_results += validate_result_list(
                items,
                f"$[{query_index}]",
                require_metadata=args.require_metadata,
                max_rank_start=args.max_rank_start,
            )

    return {
        "ok": True,
        "mode": args.mode,
        "shape": shape,
        "query_count": query_count,
        "result_count": total_results,
        "metadata_required": args.require_metadata,
    }


def main() -> int:
    args = parse_args()
    if args.require_metadata and args.mode != "encoded-search":
        print(
            "warning: --require-metadata is usually only meaningful for --mode encoded-search",
            file=sys.stderr,
        )

    try:
        payload = load_payload(args.json_path)
        summary = validate_payload(args, payload)
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

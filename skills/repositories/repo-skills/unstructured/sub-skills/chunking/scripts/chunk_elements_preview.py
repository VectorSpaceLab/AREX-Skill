#!/usr/bin/env python3
"""Preview Unstructured chunking behavior for serialized element JSON.

The input file should be readable by unstructured.staging.base.elements_from_json(). The script
prints a JSON summary that is safe to inspect before choosing parameters for indexing or RAG.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be zero or greater")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview Unstructured basic or by_title chunking for element JSON.",
    )
    parser.add_argument("elements_json", type=Path, help="JSON file produced from Unstructured elements")
    parser.add_argument(
        "--strategy",
        choices=("basic", "by_title"),
        default="by_title",
        help="Chunking strategy to preview; default: by_title",
    )
    parser.add_argument("--max-characters", type=positive_int)
    parser.add_argument("--max-tokens", type=positive_int)
    parser.add_argument("--new-after-n-chars", type=non_negative_int)
    parser.add_argument("--new-after-n-tokens", type=non_negative_int)
    parser.add_argument("--tokenizer")
    parser.add_argument("--overlap", type=non_negative_int)
    parser.add_argument("--overlap-all", type=parse_bool)
    parser.add_argument("--include-orig-elements", type=parse_bool)
    parser.add_argument("--repeat-table-headers", type=parse_bool)
    parser.add_argument("--skip-table-chunking", type=parse_bool)
    parser.add_argument("--isolate-table", type=parse_bool)
    parser.add_argument("--combine-text-under-n-chars", type=non_negative_int)
    parser.add_argument("--multipage-sections", type=parse_bool)
    parser.add_argument(
        "--show-text-preview",
        action="store_true",
        help="Include the first 120 characters of each chunk text in the summary.",
    )
    return parser


def option_dict(args: argparse.Namespace) -> dict[str, Any]:
    common = {
        "include_orig_elements": args.include_orig_elements,
        "max_characters": args.max_characters,
        "max_tokens": args.max_tokens,
        "new_after_n_chars": args.new_after_n_chars,
        "new_after_n_tokens": args.new_after_n_tokens,
        "overlap": args.overlap,
        "overlap_all": args.overlap_all,
        "tokenizer": args.tokenizer,
        "repeat_table_headers": args.repeat_table_headers,
        "skip_table_chunking": args.skip_table_chunking,
        "isolate_table": args.isolate_table,
    }
    if args.strategy == "by_title":
        common.update(
            {
                "combine_text_under_n_chars": args.combine_text_under_n_chars,
                "multipage_sections": args.multipage_sections,
            }
        )
    return {key: value for key, value in common.items() if value is not None}


def chunk_summary(chunk: Any, index: int, show_text_preview: bool) -> dict[str, Any]:
    metadata = getattr(chunk, "metadata", None)
    orig_elements = getattr(metadata, "orig_elements", None) if metadata is not None else None
    summary: dict[str, Any] = {
        "index": index,
        "category": getattr(chunk, "category", type(chunk).__name__),
        "text_length": len(getattr(chunk, "text", "") or ""),
        "orig_elements_count": None if orig_elements is None else len(orig_elements),
    }

    category = getattr(chunk, "category", type(chunk).__name__)
    if category in {"Table", "TableChunk"}:
        summary["is_table"] = True
        summary["table_chunk"] = category == "TableChunk"
        summary["table_id"] = getattr(metadata, "table_id", None)
        summary["chunk_index"] = getattr(metadata, "chunk_index", None)
        summary["is_continuation"] = getattr(metadata, "is_continuation", None)
        summary["num_carried_over_header_rows"] = getattr(
            metadata,
            "num_carried_over_header_rows",
            None,
        )
    else:
        summary["is_table"] = False

    if show_text_preview:
        text = getattr(chunk, "text", "") or ""
        summary["text_preview"] = text[:120]
    return summary


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        from unstructured.chunking.basic import chunk_elements
        from unstructured.chunking.title import chunk_by_title
        from unstructured.staging.base import elements_from_json
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Unable to import Unstructured chunking dependencies. Install unstructured with the "
            "extras needed for your document types, then rerun this preview script. Missing "
            f"module: {exc.name}"
        ) from exc

    elements = elements_from_json(filename=str(args.elements_json))
    kwargs = option_dict(args)

    chunker = chunk_by_title if args.strategy == "by_title" else chunk_elements
    chunks = chunker(elements, **kwargs)
    category_counts: dict[str, int] = {}
    for chunk in chunks:
        category = getattr(chunk, "category", type(chunk).__name__)
        category_counts[category] = category_counts.get(category, 0) + 1

    result = {
        "strategy": args.strategy,
        "options": kwargs,
        "input_elements": len(elements),
        "output_chunks": len(chunks),
        "category_counts": category_counts,
        "max_text_length": max((len(getattr(chunk, "text", "") or "") for chunk in chunks), default=0),
        "chunks": [
            chunk_summary(chunk, index, args.show_text_preview)
            for index, chunk in enumerate(chunks)
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Convert Unstructured element JSON to JSON, NDJSON, Markdown, text, or HTML."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

def _load_raw_payload(path: Path, encoding: str) -> Any:
    with path.open(encoding=encoding) as file:
        return json.load(file)


def _inspect_payload(path: Path, encoding: str) -> str:
    payload = _load_raw_payload(path, encoding)
    if not isinstance(payload, list):
        return f"top_level={type(payload).__name__}\nerror=expected JSON array of element objects\n"

    type_counts: dict[str, int] = {}
    missing_metadata = 0
    missing_text = 0
    table_with_html = 0
    table_without_html = 0
    coordinate_records = 0
    coordinate_incomplete = 0

    for item in payload:
        if not isinstance(item, dict):
            type_counts["<non-object>"] = type_counts.get("<non-object>", 0) + 1
            continue
        element_type = str(item.get("type", "<missing>"))
        type_counts[element_type] = type_counts.get(element_type, 0) + 1
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            missing_metadata += 1
            metadata = {}
        if "text" not in item and element_type != "CheckBox":
            missing_text += 1
        if element_type in {"Table", "TableChunk"}:
            if metadata.get("text_as_html"):
                table_with_html += 1
            else:
                table_without_html += 1
        coordinates = metadata.get("coordinates")
        if coordinates is not None:
            coordinate_records += 1
            if not isinstance(coordinates, dict) or not all(
                key in coordinates for key in ("points", "system", "layout_width", "layout_height")
            ):
                coordinate_incomplete += 1

    lines = [
        f"top_level=list",
        f"elements={len(payload)}",
        "types=" + ", ".join(f"{key}:{value}" for key, value in sorted(type_counts.items())),
        f"missing_metadata={missing_metadata}",
        f"missing_text={missing_text}",
        f"tables_with_text_as_html={table_with_html}",
        f"tables_without_text_as_html={table_without_html}",
        f"coordinate_records={coordinate_records}",
        f"coordinate_records_incomplete={coordinate_incomplete}",
    ]
    return "\n".join(lines) + "\n"


def _elements_to_html(elements: Iterable[Any], exclude_binary_image_data: bool, no_group_by_page: bool) -> str:
    from unstructured.partition.html.convert import elements_to_html

    return elements_to_html(
        list(elements),
        exclude_binary_image_data=exclude_binary_image_data,
        no_group_by_page=no_group_by_page,
    )


def convert_file(args: argparse.Namespace) -> str:
    input_path = Path(args.input)
    if args.inspect:
        return _inspect_payload(input_path, args.encoding)

    from unstructured.staging.base import (
        elements_from_json,
        elements_to_json,
        elements_to_md,
        elements_to_ndjson,
        elements_to_text,
    )

    elements = elements_from_json(filename=str(input_path), encoding=args.encoding)
    if args.format == "json":
        return elements_to_json(elements, indent=args.indent, encoding=args.encoding)
    if args.format == "ndjson":
        return elements_to_ndjson(elements, encoding=args.encoding)
    if args.format == "markdown":
        return elements_to_md(
            elements,
            exclude_binary_image_data=args.exclude_binary_image_data,
            encoding=args.encoding,
            normalize_formula=not args.no_normalize_formula,
            formula_markdown_style=args.formula_markdown_style,
        )
    if args.format == "text":
        text = elements_to_text(elements, encoding=args.encoding)
        return "" if text is None else text
    if args.format == "html":
        return _elements_to_html(
            elements,
            exclude_binary_image_data=args.exclude_binary_image_data,
            no_group_by_page=args.no_group_by_page,
        )
    raise ValueError(f"Unsupported format: {args.format}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a caller-provided Unstructured elements JSON file.",
    )
    parser.add_argument("input", help="Path to a JSON array of Unstructured element dictionaries.")
    parser.add_argument(
        "--format",
        choices=["json", "ndjson", "markdown", "text", "html"],
        default="json",
        help="Output format when not using --inspect. Default: json.",
    )
    parser.add_argument("--output", "-o", help="Output file. Defaults to stdout.")
    parser.add_argument("--encoding", default="utf-8", help="Input and output encoding. Default: utf-8.")
    parser.add_argument("--indent", type=int, default=4, help="JSON indentation for --format json.")
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Print schema and metadata diagnostics without rehydrating elements.",
    )
    parser.add_argument(
        "--exclude-binary-image-data",
        action="store_true",
        help="Omit embedded base64 image payloads from Markdown and HTML output.",
    )
    parser.add_argument(
        "--no-group-by-page",
        action="store_true",
        help="For HTML output, do not group elements by page.",
    )
    parser.add_argument(
        "--no-normalize-formula",
        action="store_true",
        help="For Markdown output, do not normalize common Unicode math symbols.",
    )
    parser.add_argument(
        "--formula-markdown-style",
        choices=["auto", "display_math", "plain"],
        default="auto",
        help="Formula Markdown style. Default: auto.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        output = convert_file(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding=args.encoding)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

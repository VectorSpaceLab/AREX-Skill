#!/usr/bin/env python3
"""Convert a caller-supplied Docling fixture to Markdown or JSON.

This helper uses public Docling APIs and requires only an installed Docling
package. It accepts either a path/URL with --input or in-memory text with
--string plus --input-format.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

INPUT_FORMAT_VALUES = [
    "asciidoc",
    "audio",
    "csv",
    "docx",
    "email",
    "epub",
    "html",
    "image",
    "json_docling",
    "latex",
    "md",
    "mets_gbs",
    "pdf",
    "pptx",
    "vtt",
    "xlsx",
    "xml_doclang",
    "xml_jats",
    "xml_uspto",
    "xml_xbrl",
]
STRING_FORMAT_VALUES = {"md", "html", "xml_doclang"}


def parse_headers(values: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for value in values:
        if ":" not in value:
            raise argparse.ArgumentTypeError(
                f"header must use 'Name: value' syntax, got {value!r}"
            )
        name, header_value = value.split(":", 1)
        name = name.strip()
        header_value = header_value.strip()
        if not name:
            raise argparse.ArgumentTypeError("header name must not be empty")
        headers[name] = header_value
    return headers


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def page_range(value: str) -> tuple[int, int]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("page range must use START:END syntax")
    start_text, end_text = value.split(":", 1)
    start = positive_int(start_text)
    end = positive_int(end_text)
    if end < start:
        raise argparse.ArgumentTypeError("page range end must be >= start")
    return (start, end)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a path, URL, or string fixture with Docling.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--input",
        help="Local path or URL to convert. Format is detected from the source.",
    )
    source.add_argument(
        "--string",
        help="In-memory text content to convert. Requires --input-format.",
    )
    parser.add_argument(
        "--input-format",
        choices=INPUT_FORMAT_VALUES,
        help=(
            "Restrict conversion to this InputFormat. Required for --string; "
            "for strings only md, html, and xml_doclang are supported."
        ),
    )
    parser.add_argument(
        "--name",
        help="Name used for --string conversion, e.g. note.md or page.html.",
    )
    parser.add_argument(
        "--output-format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output representation printed to stdout.",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="NAME:VALUE",
        help="HTTP header for URL input; may be supplied multiple times.",
    )
    parser.add_argument(
        "--max-num-pages",
        type=positive_int,
        default=sys.maxsize,
        help="Maximum number of pages accepted for one document.",
    )
    parser.add_argument(
        "--max-file-size",
        type=positive_int,
        default=sys.maxsize,
        help="Maximum input size in bytes.",
    )
    parser.add_argument(
        "--page-range",
        type=page_range,
        default=(1, sys.maxsize),
        metavar="START:END",
        help="Inclusive page range for paged inputs, e.g. 1:3.",
    )
    parser.add_argument(
        "--no-raise",
        action="store_true",
        help="Return captured conversion errors instead of raising immediately.",
    )
    return parser


def export_document(document: Any, output_format: str) -> str:
    if output_format == "markdown":
        return document.export_to_markdown()
    return json.dumps(document.export_to_dict(), ensure_ascii=False, indent=2)


def error_payload(message: str, details: list[str] | None = None) -> str:
    payload: dict[str, Any] = {"ok": False, "error": message}
    if details:
        payload["details"] = details
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.string is not None and args.input_format is None:
        parser.error("--string requires --input-format")
    if args.string is not None and args.input_format not in STRING_FORMAT_VALUES:
        supported = ", ".join(sorted(STRING_FORMAT_VALUES))
        parser.error(
            "--string supports only md, html, or xml_doclang. "
            f"Use --input/DocumentStream for {args.input_format!r}; "
            f"supported string formats: {supported}."
        )

    try:
        from docling.datamodel.base_models import ConversionStatus, InputFormat
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        print(
            error_payload(
                "Docling is not importable. Install the public docling package in "
                "the active Python environment before converting fixtures.",
                [str(exc)],
            ),
            file=sys.stderr,
        )
        return 2

    format_by_value = {item.value: item for item in InputFormat}
    string_formats = {
        "md": InputFormat.MD,
        "html": InputFormat.HTML,
        "xml_doclang": InputFormat.XML_DOCLANG,
    }
    success_statuses = {ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS}
    selected_format = format_by_value.get(args.input_format) if args.input_format else None
    allowed_formats = [selected_format] if selected_format is not None else None
    converter = DocumentConverter(allowed_formats=allowed_formats)

    try:
        if args.string is not None:
            result = converter.convert_string(
                args.string,
                format=string_formats[args.input_format],
                name=args.name,
            )
        else:
            source: str | Path = args.input
            if args.input and not args.input.startswith(("http://", "https://")):
                source = Path(args.input)
            result = converter.convert(
                source,
                headers=parse_headers(args.header) or None,
                raises_on_error=not args.no_raise,
                max_num_pages=args.max_num_pages,
                max_file_size=args.max_file_size,
                page_range=args.page_range,
            )
    except Exception as exc:  # noqa: BLE001 - CLI helper should report any conversion failure cleanly.
        print(error_payload(str(exc)), file=sys.stderr)
        return 2

    if result.status not in success_statuses:
        details = [error.error_message for error in result.errors]
        print(error_payload(f"conversion status: {result.status}", details), file=sys.stderr)
        return 1

    print(export_document(result.document, args.output_format))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

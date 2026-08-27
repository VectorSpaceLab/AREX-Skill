#!/usr/bin/env python3
"""Safely run Docling structured extraction on an explicit local PDF/image fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SUPPORTED_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run DocumentExtractor on a local PDF/image fixture with an explicit "
            "JSON template. The script does not download files, prefetch models, "
            "or enable remote services."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Local PDF/image fixture path to extract from.",
    )
    parser.add_argument(
        "--template-json",
        help='JSON object template, for example: {"invoice_id":"string","total":"number"}',
    )
    parser.add_argument(
        "--template-file",
        type=Path,
        help="Path to a UTF-8 JSON object template file.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum number of pages to process. Default: 1.",
    )
    parser.add_argument(
        "--page-start",
        type=int,
        default=1,
        help="1-indexed first page to process. Default: 1.",
    )
    parser.add_argument(
        "--page-end",
        type=int,
        default=1,
        help="1-indexed last page to process. Default: 1.",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=20_000_000,
        help="Maximum input file size in bytes. Default: 20000000.",
    )
    parser.add_argument(
        "--allow-non-json-template",
        action="store_true",
        help="Treat --template-json as a raw string prompt if it is not valid JSON.",
    )
    return parser


def load_template(args: argparse.Namespace) -> dict[str, Any] | str:
    if bool(args.template_json) == bool(args.template_file):
        raise ValueError("Provide exactly one of --template-json or --template-file.")

    raw_template = args.template_json
    if args.template_file:
        template_path = args.template_file.expanduser().resolve()
        if not template_path.is_file():
            raise ValueError(f"Template file does not exist: {template_path}")
        raw_template = template_path.read_text(encoding="utf-8")

    assert raw_template is not None
    try:
        parsed = json.loads(raw_template)
    except json.JSONDecodeError:
        if args.allow_non_json_template and args.template_json:
            return raw_template
        raise ValueError("Template must be a JSON object unless --allow-non-json-template is used.")

    if not isinstance(parsed, dict):
        raise ValueError("Template JSON must be an object, not an array or scalar.")
    return parsed


def validate_source(source: Path) -> Path:
    resolved = source.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"Source fixture does not exist or is not a file: {resolved}")
    if resolved.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported fixture suffix {resolved.suffix!r}. Supported: {supported}")
    return resolved


def validate_limits(args: argparse.Namespace) -> None:
    if args.max_pages < 1:
        raise ValueError("--max-pages must be at least 1.")
    if args.page_start < 1 or args.page_end < args.page_start:
        raise ValueError("Use a valid 1-indexed page range: --page-start <= --page-end.")
    if args.max_file_size < 1:
        raise ValueError("--max-file-size must be positive.")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.source:
        parser.print_help()
        return 0

    try:
        validate_limits(args)
        source = validate_source(args.source)
        template = load_template(args)

        from docling.datamodel.base_models import InputFormat
        from docling.document_extractor import DocumentExtractor

        extractor = DocumentExtractor(allowed_formats=[InputFormat.IMAGE, InputFormat.PDF])
        result = extractor.extract(
            source=source,
            template=template,
            max_num_pages=args.max_pages,
            max_file_size=args.max_file_size,
            page_range=(args.page_start, args.page_end),
        )

        print(
            json.dumps(
                {
                    "status": str(result.status),
                    "errors": [error.model_dump() for error in result.errors],
                    "pages": [page.model_dump() for page in result.pages],
                },
                indent=2,
                default=str,
            )
        )
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Convert office documents to Markdown through the public PaddleOCR API."""

from __future__ import annotations

import argparse
from pathlib import Path

from paddleocr import doc2md_convert, doc2md_supported_formats


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert an office document to Markdown.")
    parser.add_argument("source", nargs="?", help="Source .docx, .pptx, or .xlsx file.")
    parser.add_argument("--output", default=None, help="Optional Markdown output path.")
    parser.add_argument("--formats", action="store_true", help="List supported formats and exit.")
    parser.add_argument("--no-drawings", action="store_true", help="Skip drawing-layer extraction for docx/xlsx.")
    parser.add_argument("--no-headers-footers", action="store_true", help="Skip DOCX header/footer extraction.")
    parser.add_argument("--sheet-name", default=None, help="Convert only one XLSX sheet by name.")
    parser.add_argument("--max-rows", type=int, default=None, help="Limit the number of XLSX rows converted per sheet.")
    args = parser.parse_args()

    if args.formats:
        print(", ".join(f".{item}" for item in doc2md_supported_formats()))
        return 0

    if not args.source:
        parser.error("source is required unless --formats is set")

    converter_kwargs: dict[str, object] = {}
    if args.no_drawings:
        converter_kwargs["extract_drawings"] = False
    if args.no_headers_footers:
        converter_kwargs["extract_headers_footers"] = False
    if args.sheet_name is not None:
        converter_kwargs["sheet_name"] = args.sheet_name
    if args.max_rows is not None:
        converter_kwargs["max_rows"] = args.max_rows

    result = doc2md_convert(args.source, output=args.output, **converter_kwargs)
    if args.output:
        print(str(Path(args.output)))
    else:
        print(result.markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

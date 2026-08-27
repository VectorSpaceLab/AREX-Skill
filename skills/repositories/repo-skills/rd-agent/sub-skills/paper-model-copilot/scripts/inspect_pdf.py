#!/usr/bin/env python3
"""Inspect a local PDF without mutating it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def inspect_with_pymupdf(path: Path) -> dict[str, object]:
    import fitz  # type: ignore

    doc = fitz.open(str(path))
    try:
        text = doc[0].get_text("text") if len(doc) else ""
        return {"backend": "fitz", "pages": len(doc), "first_page_text_preview": text[:1000]}
    finally:
        doc.close()


def inspect_with_pypdf(path: Path) -> dict[str, object]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    first = reader.pages[0].extract_text() if reader.pages else ""
    return {"backend": "pypdf", "pages": len(reader.pages), "first_page_text_preview": (first or "")[:1000]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    if not args.pdf.exists():
        raise SystemExit(f"missing file: {args.pdf}")
    try:
        result = inspect_with_pymupdf(args.pdf)
    except Exception:
        result = inspect_with_pypdf(args.pdf)
    result["path"] = str(args.pdf)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

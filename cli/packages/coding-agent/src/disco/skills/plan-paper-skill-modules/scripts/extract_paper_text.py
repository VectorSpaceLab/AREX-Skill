#!/usr/bin/env python3
"""Extract text from a paper PDF or text file."""

from __future__ import annotations

import argparse
from pathlib import Path


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"pypdf is required to read PDF files: {exc}") from exc

    reader = PdfReader(str(path))
    chunks = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        chunks.append(f"\n\n--- Page {idx} ---\n\n{clean_text(text).strip()}")
    return clean_text("\n".join(chunks).strip()) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="PDF or text paper path.")
    parser.add_argument("--output", required=True, help="Output text path.")
    args = parser.parse_args()

    paper = Path(args.paper).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if paper.suffix.lower() == ".pdf":
        text = extract_pdf(paper)
    else:
        text = clean_text(paper.read_text(encoding="utf-8", errors="replace"))

    output.write_text(text, encoding="utf-8")
    print(f"wrote {output} ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

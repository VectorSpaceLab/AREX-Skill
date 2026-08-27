#!/usr/bin/env python3
"""No-network PaperQA text/Markdown parse-and-chunk smoke.

Creates a tiny text fixture or reads a supplied local path, parses it with
paperqa.readers.parse_text, chunks it with chunk_text, and prints JSON. It does
not call embeddings, LLMs, metadata providers, PDF readers, or Office parsers.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from paperqa.readers import chunk_text, parse_text
from paperqa.types import Doc

SAMPLE_TEXT = """# PaperQA parsing smoke

This tiny local document is long enough to exercise chunking.
It contains Markdown-style headings, plain prose, and repeated terms.
PaperQA should parse it as local text without network access.
"""


def summarize_chunks(chunks: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": chunk.name,
            "chars": len(chunk.text),
            "preview": chunk.text[:80].replace("\n", "\\n"),
            "media_count": len(getattr(chunk, "media", []) or []),
        }
        for chunk in chunks
    ]


def run_smoke(
    path: Path,
    *,
    html: bool,
    split_lines: bool,
    chunk_chars: int,
    overlap: int,
    citation: str,
    docname: str | None,
) -> dict[str, Any]:
    parsed = parse_text(path, html=html, split_lines=split_lines)
    if split_lines:
        # chunk_text intentionally requires string content; for line-based code
        # chunking use read_doc or chunk_code_text. This script keeps the main
        # smoke on parse_text+chunk_text as requested.
        content_for_chunk = "".join(parsed.content) if isinstance(parsed.content, list) else parsed.content
        parsed = type(parsed)(content=content_for_chunk, metadata=parsed.metadata)
    doc = Doc(docname=docname or path.stem or "paperqa-smoke", citation=citation, dockey="paperqa-smoke")
    chunks = chunk_text(parsed, doc, chunk_chars=chunk_chars, overlap=overlap)
    return {
        "path_name": path.name,
        "html": html,
        "split_lines_input": split_lines,
        "parsed_content_type": type(parsed.content).__name__,
        "parsed_chars": parsed.metadata.total_parsed_text_length,
        "parsing_libraries": parsed.metadata.parsing_libraries,
        "metadata_name": parsed.metadata.name,
        "chunk_count": len(chunks),
        "chunks": summarize_chunks(chunks),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="Optional local text/Markdown/HTML file to parse.")
    parser.add_argument("--html", action="store_true", help="Parse the input as HTML via html2text.")
    parser.add_argument("--markdown", action="store_true", help="Use a temporary .md sample instead of .txt when --path is omitted.")
    parser.add_argument("--split-lines", action="store_true", help="Exercise parse_text(split_lines=True), then join for chunk_text smoke.")
    parser.add_argument("--chunk-chars", type=int, default=120, help="Chunk size for chunk_text.")
    parser.add_argument("--overlap", type=int, default=20, help="Chunk overlap for chunk_text.")
    parser.add_argument("--citation", default="Local parse smoke", help="Citation stored on the synthetic Doc object.")
    parser.add_argument("--docname", help="Optional Doc.docname to use in chunk names.")
    args = parser.parse_args()

    if args.chunk_chars <= 0:
        raise SystemExit("--chunk-chars must be positive for chunk_text")
    if args.overlap < 0:
        raise SystemExit("--overlap must be non-negative")
    if args.overlap >= args.chunk_chars:
        raise SystemExit("--overlap must be smaller than --chunk-chars")

    if args.path:
        path = args.path
        if not path.exists() or not path.is_file():
            raise SystemExit(f"Input path is not a file: {path}")
        result = run_smoke(
            path,
            html=args.html,
            split_lines=args.split_lines,
            chunk_chars=args.chunk_chars,
            overlap=args.overlap,
            citation=args.citation,
            docname=args.docname,
        )
    else:
        suffix = ".md" if args.markdown else ".txt"
        with tempfile.TemporaryDirectory(prefix="paperqa-parse-smoke-") as tmpdir:
            path = Path(tmpdir) / f"sample{suffix}"
            path.write_text(SAMPLE_TEXT, encoding="utf-8")
            result = run_smoke(
                path,
                html=args.html,
                split_lines=args.split_lines,
                chunk_chars=args.chunk_chars,
                overlap=args.overlap,
                citation=args.citation,
                docname=args.docname or "sample",
            )

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["chunk_count"] < 1:
        raise SystemExit("Expected at least one chunk")
    if result["parsed_chars"] <= 0:
        raise SystemExit("Expected non-empty parsed text")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

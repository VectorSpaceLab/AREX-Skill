#!/usr/bin/env python3
"""Deterministic local smoke test for Chonkie pipeline processing.

The script creates temporary fixtures and verifies direct text, file, directory,
markdown, overlap, and JSON export behavior. It intentionally avoids network
calls, model downloads, credentials, provider APIs, and datastore writes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic Chonkie Pipeline smoke test using only local "
            "text/markdown/recursive/overlap/JSON behavior."
        )
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary fixture/output directory and print its path.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final JSON summary.",
    )
    return parser


def _assert_document(obj: Any, *, label: str) -> None:
    from chonkie import Document

    assert isinstance(obj, Document), f"{label}: expected Document, got {type(obj)!r}"
    assert hasattr(obj, "content"), f"{label}: missing content"
    assert hasattr(obj, "chunks"), f"{label}: missing chunks"
    assert isinstance(obj.chunks, list), f"{label}: chunks is not a list"
    assert obj.chunks, f"{label}: expected at least one chunk"
    for idx, chunk in enumerate(obj.chunks):
        assert isinstance(chunk.text, str), f"{label}: chunk {idx} text is not str"
        assert chunk.token_count >= 0, f"{label}: chunk {idx} token_count is negative"


def _make_fixtures(root: Path) -> dict[str, Path]:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    text_path = docs_dir / "alpha.txt"
    text_path.write_text(
        (
            "Alpha introduction for a local text file.\n\n"
            "Second paragraph has enough repeated words to force deterministic "
            "recursive word chunks in the smoke test. "
            "pipeline chunk overlap local deterministic behavior " * 10
        ),
        encoding="utf-8",
    )

    markdown_path = docs_dir / "beta.md"
    markdown_path.write_text(
        """# Beta Report

A markdown paragraph with table, code, and image evidence.

| Metric | Value |
| --- | --- |
| Precision | 0.91 |
| Recall | 0.88 |

```python
print("beta")
```

![chart](chart.png)

Final paragraph for recursive chunking.
""",
        encoding="utf-8",
    )

    ignored_path = docs_dir / "ignored.bin"
    ignored_path.write_bytes(b"\x00\x01not text")

    return {"docs_dir": docs_dir, "text_path": text_path, "markdown_path": markdown_path}


def run_smoke(root: Path, quiet: bool = False) -> dict[str, Any]:
    from chonkie import MarkdownDocument, Pipeline

    fixtures = _make_fixtures(root)
    text_path = fixtures["text_path"]
    markdown_path = fixtures["markdown_path"]
    docs_dir = fixtures["docs_dir"]

    direct_text = (
        "Direct pipeline text with paragraph boundaries.\n\n"
        + "recursive chunking should remain local and deterministic. " * 24
    )

    direct_doc = (
        Pipeline()
        .process_with("text")
        .chunk_with("recursive", tokenizer="word", chunk_size=18, min_characters_per_chunk=1)
        .run(texts=direct_text)
    )
    _assert_document(direct_doc, label="direct text")
    assert direct_doc.content == direct_text, "direct text: content changed"

    # Define steps in non-CHOMP order to prove automatic ordering before execution.
    ordering_pipe = (
        Pipeline()
        .refine_with(
            "overlap",
            tokenizer="word",
            context_size=2,
            mode="token",
            method="suffix",
            merge=False,
            inplace=False,
        )
        .chunk_with("recursive", tokenizer="word", chunk_size=14, min_characters_per_chunk=1)
        .process_with("text")
    )
    description = ordering_pipe.describe()
    assert description.startswith("process(text) -> chunk(recursive) -> refine(overlap)"), description
    ordered_doc = ordering_pipe.run(texts=direct_text)
    _assert_document(ordered_doc, label="ordered overlap")
    if len(ordered_doc.chunks) > 1:
        assert hasattr(ordered_doc.chunks[0], "context"), "ordered overlap: first chunk missing context"
        assert ordered_doc.chunks[0].context, "ordered overlap: empty context"

    file_doc = (
        Pipeline()
        .fetch_from("file", path=text_path)
        .chunk_with("recursive", tokenizer="word", chunk_size=20, min_characters_per_chunk=1)
        .run()
    )
    _assert_document(file_doc, label="single file")
    assert file_doc.metadata.get("filename") == text_path.name, "single file: filename metadata missing"

    batch_docs = (
        Pipeline()
        .fetch_from("file", dir=docs_dir, ext=[".txt", ".md"])
        .process_with("text")
        .chunk_with("recursive", tokenizer="word", chunk_size=24, min_characters_per_chunk=1)
        .run()
    )
    assert isinstance(batch_docs, list), f"directory: expected list, got {type(batch_docs)!r}"
    assert len(batch_docs) == 2, f"directory: expected 2 filtered docs, got {len(batch_docs)}"
    for idx, doc in enumerate(batch_docs):
        _assert_document(doc, label=f"directory doc {idx}")
        assert doc.metadata.get("filename") in {text_path.name, markdown_path.name}

    markdown_doc = (
        Pipeline()
        .fetch_from("file", path=markdown_path)
        .process_with("markdown", tokenizer="word")
        .chunk_with("recursive", tokenizer="word", chunk_size=24, min_characters_per_chunk=1)
        .run()
    )
    _assert_document(markdown_doc, label="markdown")
    assert isinstance(markdown_doc, MarkdownDocument), f"markdown: got {type(markdown_doc)!r}"
    assert markdown_doc.tables, "markdown: expected extracted table"
    assert markdown_doc.code, "markdown: expected extracted code block"
    assert markdown_doc.images, "markdown: expected extracted image"

    export_path = root / "chunks.jsonl"
    export_doc = (
        Pipeline()
        .chunk_with("recursive", tokenizer="word", chunk_size=16, min_characters_per_chunk=1)
        .export_with("json", file=export_path)
        .run(texts="JSON export text. " * 20)
    )
    _assert_document(export_doc, label="json export")
    assert export_path.is_file(), "json export: output file missing"
    lines = export_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(export_doc.chunks), "json export: line count does not match chunks"
    first_record = json.loads(lines[0])
    assert "text" in first_record and "token_count" in first_record, "json export: bad record shape"

    try:
        Pipeline().process_with("text").run(texts="missing chunker")
    except ValueError as exc:
        assert "chunker" in str(exc).lower(), f"validation: unexpected error {exc!r}"
    else:
        raise AssertionError("validation: missing chunker did not fail")

    summary = {
        "status": "ok",
        "temp_dir": str(root),
        "direct_chunks": len(direct_doc.chunks),
        "ordered_chunks": len(ordered_doc.chunks),
        "file_chunks": len(file_doc.chunks),
        "directory_docs": len(batch_docs),
        "markdown_tables": len(markdown_doc.tables),
        "markdown_code_blocks": len(markdown_doc.code),
        "markdown_images": len(markdown_doc.images),
        "json_lines": len(lines),
        "pipeline_description": description,
    }
    if not quiet:
        print("Chonkie pipeline smoke passed.")
    return summary


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    temp_root = Path(tempfile.mkdtemp(prefix="chonkie-pipeline-smoke-"))
    try:
        summary = run_smoke(temp_root, quiet=args.quiet)
        print(json.dumps(summary, indent=2, sort_keys=True))
    finally:
        if args.keep_temp:
            print(f"Kept temporary directory: {temp_root}")
        else:
            shutil.rmtree(temp_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

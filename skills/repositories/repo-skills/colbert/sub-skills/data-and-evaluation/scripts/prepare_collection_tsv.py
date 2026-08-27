#!/usr/bin/env python3
"""Prepare a ColBERT passage collection TSV from document TSV rows."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


FORMATS = {
    "docid,text": ("docid", "text"),
    "docid,text,title": ("docid", "text", "title"),
    "docid,url,title,text": ("docid", "url", "title", "text"),
}


class PreparationError(ValueError):
    """Raised when input documents cannot be converted safely."""


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\t", " ").split())


def passage_spans(words: list[str], nwords: int, overlap: int, wrap_last: bool) -> list[list[str]]:
    if not words:
        return []
    if len(words) <= nwords:
        return [words]
    step = nwords - overlap
    if step <= 0:
        raise PreparationError("overlap must be smaller than nwords")
    spans = [words[offset : offset + nwords] for offset in range(0, len(words), step)]
    if not wrap_last:
        return [span for span in spans if span]

    fixed = []
    for span in spans:
        if len(span) == nwords:
            fixed.append(span)
        elif fixed:
            fixed.append(words[-nwords:])
        else:
            fixed.append(span)

    deduped = []
    for span in fixed:
        if not deduped or span != deduped[-1]:
            deduped.append(span)
    return deduped


def iter_documents(path: Path, input_format: str, has_header: bool):
    columns = FORMATS[input_format]
    text_index = columns.index("text")
    docid_index = columns.index("docid")
    title_index = columns.index("title") if "title" in columns else None

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, start=1):
            if has_header and line_number == 1:
                continue
            if not row or all(cell == "" for cell in row):
                continue
            if len(row) != len(columns):
                raise PreparationError(f"{path}:{line_number}: expected {len(columns)} columns for {input_format}, got {len(row)}")
            docid = row[docid_index]
            text = normalize_text(row[text_index])
            title = normalize_text(row[title_index]) if title_index is not None else ""
            if not docid:
                raise PreparationError(f"{path}:{line_number}: empty docid")
            if not text:
                raise PreparationError(f"{path}:{line_number}: empty text")
            yield line_number, docid, title, text


def write_collection(args: argparse.Namespace) -> dict[str, int]:
    if args.output.exists() and not args.overwrite:
        raise PreparationError(f"output exists: {args.output}")
    if args.nwords < 1:
        raise PreparationError("nwords must be positive")
    if args.overlap < 0 or args.overlap >= args.nwords:
        raise PreparationError("overlap must be >= 0 and smaller than nwords")
    if args.include_title and "title" not in FORMATS[args.format]:
        raise PreparationError("--include-title requires an input format with title")
    if args.prepend_title and "title" not in FORMATS[args.format]:
        raise PreparationError("--prepend-title requires an input format with title")

    documents = 0
    passages = 0
    skipped_short = 0
    duplicate_docids = 0
    seen_docids: set[str] = set()

    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        if args.output_header:
            header = ["id", "text"]
            if args.include_title:
                header.append("title")
            if args.include_docid:
                header.append("docid")
            writer.writerow(header)

        next_pid = args.start_pid
        for _, docid, title, text in iter_documents(args.input, args.format, args.has_header):
            documents += 1
            if docid in seen_docids:
                duplicate_docids += 1
            seen_docids.add(docid)

            words = text.split()
            if len(words) < args.min_words:
                skipped_short += 1
                continue
            spans = passage_spans(words, args.nwords, args.overlap, args.wrap_last)
            for span in spans:
                passage = " ".join(span)
                if args.prepend_title and title:
                    passage = f"{title} | {passage}"
                row: list[int | str] = [next_pid, passage]
                if args.include_title:
                    row.append(title)
                if args.include_docid:
                    row.append(docid)
                writer.writerow(row)
                next_pid += 1
                passages += 1

    return {
        "documents": documents,
        "passages": passages,
        "skipped_short_documents": skipped_short,
        "duplicate_docids": duplicate_docids,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert document TSV files into ColBERT passage collection TSV files with whitespace splitting.",
        epilog=(
            "Example: python prepare_collection_tsv.py --input docs.tsv --output collection.tsv "
            "--format docid,text --nwords 100 --overlap 20"
        ),
    )
    parser.add_argument("--input", required=True, type=Path, help="Input document TSV")
    parser.add_argument("--output", required=True, type=Path, help="Output passage TSV")
    parser.add_argument("--format", required=True, choices=sorted(FORMATS), help="Input TSV column format")
    parser.add_argument("--has-header", action="store_true", help="Skip the first input row")
    parser.add_argument("--output-header", action="store_true", help="Write an output header row")
    parser.add_argument("--nwords", type=int, default=100, help="Maximum whitespace words per passage")
    parser.add_argument("--overlap", type=int, default=0, help="Whitespace word overlap between adjacent passages")
    parser.add_argument("--min-words", type=int, default=1, help="Skip documents shorter than this many words")
    parser.add_argument("--start-pid", type=int, default=0, help="First output passage id")
    parser.add_argument("--wrap-last", action="store_true", help="Make the final passage use the last nwords, similar to native docs2passages")
    parser.add_argument("--prepend-title", action="store_true", help="Prefix title text to each passage when input has a title")
    parser.add_argument("--include-title", action="store_true", help="Append title as an output column for inspection workflows")
    parser.add_argument("--include-docid", action="store_true", help="Append source docid as an output column for mapping workflows")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output")
    args = parser.parse_args()

    try:
        summary = write_collection(args)
        print(
            "documents={documents} passages={passages} skipped_short_documents={skipped_short_documents} "
            "duplicate_docids={duplicate_docids} output={output}".format(output=args.output, **summary)
        )
        return 0
    except PreparationError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

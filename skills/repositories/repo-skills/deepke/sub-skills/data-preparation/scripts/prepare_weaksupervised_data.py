#!/usr/bin/env python3
"""Standalone dictionary-based NER weak-supervision helper for DeepKE BIO data.

Generated helper for the DeepKE data-preparation skill. It intentionally avoids
source-checkout imports and external tokenizer state; matching is deterministic
longest-surface matching from a CSV dictionary.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

Span = Tuple[int, int, str]
Entry = Tuple[str, str]


class DataPrepError(ValueError):
    """User-facing data-preparation failure."""


def ensure_parent(path: Path) -> None:
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)


def load_dictionary(path: Path, *, encoding: str) -> List[Entry]:
    try:
        with path.open("r", encoding=encoding, newline="") as fh:
            rows = list(csv.reader(fh))
    except OSError as exc:
        raise DataPrepError(f"cannot read dictionary {path}: {exc}") from exc
    if not rows:
        raise DataPrepError("dictionary CSV is empty")

    start = 0
    header = [cell.strip().lower() for cell in rows[0]]
    if len(header) >= 2 and header[0] in {"entity", "word", "surface", "text"} and header[1] in {"label", "tag", "type"}:
        start = 1

    entries: List[Entry] = []
    seen = set()
    for line_no, row in enumerate(rows[start:], start + 1):
        if len(row) < 2:
            raise DataPrepError(f"dictionary row {line_no} has {len(row)} column(s), expected at least 2")
        entity = row[0].strip()
        label = row[1].strip()
        if not entity or not label:
            continue
        key = (entity, label)
        if key not in seen:
            entries.append(key)
            seen.add(key)
    if not entries:
        raise DataPrepError("dictionary contains no nonempty entity,label rows")
    return entries


def read_source_lines(source_dir: Path | None, source_file: Path | None, *, encoding: str) -> List[str]:
    paths: List[Path] = []
    if source_file is not None:
        paths = [source_file]
    elif source_dir is not None:
        if not source_dir.exists() or not source_dir.is_dir():
            raise DataPrepError(f"source directory does not exist or is not a directory: {source_dir}")
        paths = sorted(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() == ".txt")
        if not paths:
            raise DataPrepError(f"source directory contains no .txt files: {source_dir}")
    else:
        raise DataPrepError("provide --source-dir or --source-file")

    lines: List[str] = []
    for path in paths:
        try:
            with path.open("r", encoding=encoding) as fh:
                for raw in fh:
                    line = raw.strip()
                    if line:
                        lines.append(line)
        except OSError as exc:
            raise DataPrepError(f"cannot read source text {path}: {exc}") from exc
    if not lines:
        raise DataPrepError("source text contains no nonempty lines")
    return lines


def normalize(text: str, *, case_sensitive: bool) -> str:
    return text if case_sensitive else text.lower()


def find_dictionary_spans(text: str, entries: Sequence[Entry], *, case_sensitive: bool) -> List[Span]:
    haystack = normalize(text, case_sensitive=case_sensitive)
    occupied = [False] * len(text)
    spans: List[Span] = []

    # Longer surfaces win over shorter overlapping surfaces; ties are stable by label/name.
    ordered = sorted(entries, key=lambda item: (-len(item[0]), item[0], item[1]))
    for surface, label in ordered:
        needle = normalize(surface, case_sensitive=case_sensitive)
        start = 0
        while True:
            idx = haystack.find(needle, start)
            if idx < 0:
                break
            end = idx + len(surface)
            if end <= len(text) and not any(occupied[idx:end]):
                spans.append((idx, end, label))
                for pos in range(idx, end):
                    occupied[pos] = True
            start = idx + max(1, len(needle))
    return sorted(spans, key=lambda item: (item[0], item[1]))


def char_units(text: str) -> List[Tuple[str, int, int]]:
    return [(ch, i, i + 1) for i, ch in enumerate(text) if ch not in "\r\n"]


def token_units(text: str) -> List[Tuple[str, int, int]]:
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(r"\w+|[^\w\s]", text, flags=re.UNICODE)]


def choose_units(text: str, *, language: str, unit: str) -> List[Tuple[str, int, int]]:
    if unit == "char" or (unit == "auto" and language == "cn"):
        return char_units(text)
    return token_units(text)


def labels_for_units(units: Sequence[Tuple[str, int, int]], spans: Sequence[Span]) -> List[str]:
    labels: List[str] = []
    for _, start, end in units:
        label = "O"
        for span_start, span_end, span_label in spans:
            if end <= span_start or start >= span_end:
                continue
            prefix = "B" if start == span_start else "I"
            label = f"{prefix}-{span_label}"
            break
        labels.append(label)
    return labels


def split_counts(total: int, rates: Sequence[float]) -> List[int]:
    if any(rate < 0 for rate in rates):
        raise DataPrepError("split rates must be nonnegative")
    if abs(sum(rates) - 1.0) > 1e-6:
        raise DataPrepError(f"split rates must sum to 1.0, got {sum(rates):.8f}")
    raw = [total * rate for rate in rates]
    counts = [int(value) for value in raw]
    remaining = total - sum(counts)
    order = sorted(range(len(rates)), key=lambda idx: (raw[idx] - counts[idx], rates[idx]), reverse=True)
    for idx in order[:remaining]:
        counts[idx] += 1
    return counts


def write_bio_file(path: Path, records: Sequence[Tuple[str, List[Span]]], *, language: str, unit: str, encoding: str) -> None:
    ensure_parent(path)
    with path.open("w", encoding=encoding, newline="\n") as fh:
        for record_index, (text, spans) in enumerate(records):
            units = choose_units(text, language=language, unit=unit)
            labels = labels_for_units(units, spans)
            for (piece, _, _), label in zip(units, labels):
                fh.write(f"{piece} {label}\n")
            if record_index != len(records) - 1:
                fh.write("\n")


def prepare(args: argparse.Namespace) -> None:
    source_dir = Path(args.source_dir) if args.source_dir and not args.source_file else None
    source_file = Path(args.source_file) if args.source_file else None
    entries = load_dictionary(Path(args.dict_file), encoding=args.encoding)
    lines = read_source_lines(source_dir, source_file, encoding=args.encoding)

    if args.case_sensitive is None:
        case_sensitive = args.language == "cn"
    else:
        case_sensitive = args.case_sensitive

    records = [(line, find_dictionary_spans(line, entries, case_sensitive=case_sensitive)) for line in lines]
    if args.shuffle:
        random.Random(args.seed).shuffle(records)

    counts = split_counts(len(records), [args.train_rate, args.dev_rate, args.test_rate])
    names = ["train", "dev", "test"]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    offset = 0
    summary: Dict[str, Dict[str, int]] = {}
    for name, count in zip(names, counts):
        split_records = records[offset : offset + count]
        offset += count
        out = output_dir / f"{args.output_prefix}_{args.language}_{name}.txt"
        write_bio_file(out, split_records, language=args.language, unit=args.unit, encoding=args.encoding)
        mention_count = sum(len(spans) for _, spans in split_records)
        summary[name] = {"records": len(split_records), "dictionary_mentions": mention_count}
        if count == 0:
            print(f"warning: {name} split is empty; use more data or different rates", file=sys.stderr)

    print(json.dumps({"output_dir": str(output_dir), "files": summary}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create DeepKE BIO NER train/dev/test files by deterministic dictionary weak supervision.",
    )
    parser.add_argument("--language", choices=["cn", "en"], default="cn", help="language hint; cn defaults to char BIO, en to token BIO")
    parser.add_argument("--source-dir", default="source_data", help="directory containing .txt source files (default: source_data)")
    parser.add_argument("--source-file", help="single .txt source file; overrides --source-dir")
    parser.add_argument("--dict-file", default="vocab_dict.csv", help="CSV with entity,label rows (default: vocab_dict.csv)")
    parser.add_argument("--output-dir", default=".", help="directory for generated split files (default: current directory)")
    parser.add_argument("--output-prefix", default="deepke_weak", help="prefix for generated files (default: deepke_weak)")
    parser.add_argument("--train-rate", type=float, default=0.8, help="training split rate (default: 0.8)")
    parser.add_argument("--dev-rate", type=float, default=0.1, help="development split rate (default: 0.1)")
    parser.add_argument("--test-rate", type=float, default=0.1, help="test split rate (default: 0.1)")
    parser.add_argument("--seed", type=int, default=42, help="shuffle seed when --no-shuffle is not used (default: 42)")
    parser.add_argument("--no-shuffle", dest="shuffle", action="store_false", help="preserve source-line order instead of shuffling")
    parser.set_defaults(shuffle=True)
    parser.add_argument("--unit", choices=["auto", "char", "token"], default="auto", help="BIO output unit (default: auto)")
    case = parser.add_mutually_exclusive_group()
    case.add_argument("--case-sensitive", dest="case_sensitive", action="store_true", help="match dictionary entries case-sensitively")
    case.add_argument("--case-insensitive", dest="case_sensitive", action="store_false", help="match dictionary entries case-insensitively")
    parser.set_defaults(case_sensitive=None)
    parser.add_argument("--encoding", default="utf-8", help="text/CSV encoding (default: utf-8)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        prepare(args)
    except DataPrepError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

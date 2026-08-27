#!/usr/bin/env python3
"""Standalone distant-supervision relation labeler for DeepKE RE data.

Generated helper for the DeepKE data-preparation skill. It labels source
candidate pairs from a CSV triple table without importing DeepKE or depending on
any source checkout.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

Triple = Tuple[str, str, str]


class DataPrepError(ValueError):
    """User-facing data-preparation failure."""


def read_json_records(path: Path, *, json_lines: bool, encoding: str) -> List[Dict[str, Any]]:
    try:
        text = path.read_text(encoding=encoding)
    except OSError as exc:
        raise DataPrepError(f"cannot read source file {path}: {exc}") from exc
    try:
        if json_lines:
            records: List[Dict[str, Any]] = []
            for line_no, line in enumerate(text.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise DataPrepError(f"JSONL line {line_no} is {type(value).__name__}, expected object")
                records.append(value)
            return records
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DataPrepError(f"invalid JSON in {path}: line {exc.lineno} column {exc.colno}: {exc.msg}") from exc
    if isinstance(value, list):
        if not all(isinstance(item, dict) for item in value):
            raise DataPrepError("source JSON array must contain objects")
        return list(value)
    if isinstance(value, dict):
        return [value]
    raise DataPrepError(f"source JSON must be an object or array, got {type(value).__name__}")


def load_triples(path: Path, *, encoding: str) -> List[Triple]:
    try:
        with path.open("r", encoding=encoding, newline="") as fh:
            rows = list(csv.reader(fh))
    except OSError as exc:
        raise DataPrepError(f"cannot read triple file {path}: {exc}") from exc
    if not rows:
        raise DataPrepError("triple CSV is empty")

    start = 0
    header = [cell.strip().lower() for cell in rows[0]]
    if len(header) >= 3 and header[0] in {"head", "subject", "h"} and header[1] in {"tail", "object", "t"} and header[2] in {"rel", "relation", "predicate", "label"}:
        start = 1

    triples: List[Triple] = []
    for line_no, row in enumerate(rows[start:], start + 1):
        if len(row) < 3:
            raise DataPrepError(f"triple row {line_no} has {len(row)} column(s), expected at least 3")
        head, tail, relation = row[0].strip(), row[1].strip(), row[2].strip()
        if not head or not tail or not relation:
            continue
        triples.append((head, tail, relation))
    if not triples:
        raise DataPrepError("triple CSV contains no nonempty head,tail,relation rows")
    return triples


def normalize(value: str, *, language: str, case_sensitive: bool | None) -> str:
    if case_sensitive is None:
        case_sensitive = language == "cn"
    return value if case_sensitive else value.lower()


def build_relation_index(
    triples: Sequence[Triple],
    *,
    language: str,
    case_sensitive: bool | None,
    bidirectional: bool,
) -> Dict[Tuple[str, str], str]:
    index: Dict[Tuple[str, str], str] = {}
    for head, tail, relation in triples:
        key = (normalize(head, language=language, case_sensitive=case_sensitive), normalize(tail, language=language, case_sensitive=case_sensitive))
        index.setdefault(key, relation)
        if bidirectional:
            reverse_key = (key[1], key[0])
            index.setdefault(reverse_key, relation)
    return index


def validate_record(record: Dict[str, Any], *, index: int, strict_offsets: bool) -> Tuple[str, str, str]:
    for field in ("sentence", "head", "tail"):
        if field not in record:
            raise DataPrepError(f"record {index} is missing required field {field!r}")
        if not isinstance(record[field], str):
            raise DataPrepError(f"record {index} field {field!r} must be a string")
    sentence = record["sentence"]
    head = record["head"]
    tail = record["tail"]

    def check_offset(name: str, surface: str) -> None:
        if name not in record or record[name] in (None, ""):
            return
        try:
            offset = int(record[name])
        except (TypeError, ValueError) as exc:
            raise DataPrepError(f"record {index} field {name!r} must be an integer offset") from exc
        actual = sentence[offset : offset + len(surface)] if 0 <= offset <= len(sentence) else ""
        if actual != surface:
            message = f"record {index} {name}={offset} slices {actual!r}, expected {surface!r}"
            if strict_offsets:
                raise DataPrepError(message)
            print(f"warning: {message}", file=sys.stderr)

    check_offset("head_offset", head)
    check_offset("tail_offset", tail)
    return sentence, head, tail


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


def ensure_parent(path: Path) -> None:
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, records: Sequence[Dict[str, Any]], *, encoding: str) -> None:
    ensure_parent(path)
    with path.open("w", encoding=encoding) as fh:
        json.dump(list(records), fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def label_data(args: argparse.Namespace) -> None:
    source = read_json_records(Path(args.source_file), json_lines=args.json_lines, encoding=args.encoding)
    if not source:
        raise DataPrepError("source file contains no records")
    triples = load_triples(Path(args.triple_file), encoding=args.encoding)
    relation_index = build_relation_index(
        triples,
        language=args.language,
        case_sensitive=args.case_sensitive,
        bidirectional=args.bidirectional,
    )

    labeled: List[Dict[str, Any]] = []
    matched = 0
    for idx, record in enumerate(source):
        _, head, tail = validate_record(record, index=idx, strict_offsets=args.strict_offsets)
        key = (
            normalize(head, language=args.language, case_sensitive=args.case_sensitive),
            normalize(tail, language=args.language, case_sensitive=args.case_sensitive),
        )
        relation = relation_index.get(key, args.none_label)
        if relation != args.none_label:
            matched += 1
        new_record = dict(record)
        new_record["relation"] = relation
        labeled.append(new_record)

    if args.shuffle:
        random.Random(args.seed).shuffle(labeled)

    counts = split_counts(len(labeled), [args.train_rate, args.dev_rate, args.test_rate])
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    names = ["train", "dev", "test"]

    offset = 0
    files: Dict[str, Dict[str, Any]] = {}
    for name, count in zip(names, counts):
        split = labeled[offset : offset + count]
        offset += count
        out = output_dir / f"{args.output_prefix}_{name}.json"
        write_json(out, split, encoding=args.encoding)
        files[name] = {"records": len(split), "path": str(out)}
        if count == 0:
            print(f"warning: {name} split is empty; use more data or different rates", file=sys.stderr)

    print(json.dumps({"records": len(labeled), "matched": matched, "none_label": args.none_label, "files": files}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assign DeepKE RE relation labels to source candidate pairs using a head,tail,relation triple CSV.",
    )
    parser.add_argument("--language", choices=["en", "cn"], default="en", help="language hint; English defaults to case-insensitive matching")
    parser.add_argument("--source-file", default="source_data.json", help="JSON/JSONL source candidate-pair file (default: source_data.json)")
    parser.add_argument("--triple-file", default="triple_file.csv", help="CSV triple file with head,tail,rel columns (default: triple_file.csv)")
    parser.add_argument("--json-lines", action="store_true", help="read one JSON object per nonempty line from --source-file")
    parser.add_argument("--output-dir", default=".", help="directory for labeled split files (default: current directory)")
    parser.add_argument("--output-prefix", default="deepke_ds_labeled", help="prefix for output files (default: deepke_ds_labeled)")
    parser.add_argument("--none-label", default="None", help="relation label for unmatched pairs (default: None)")
    parser.add_argument("--train-rate", type=float, default=0.8, help="training split rate (default: 0.8)")
    parser.add_argument("--dev-rate", type=float, default=0.1, help="development split rate (default: 0.1)")
    parser.add_argument("--test-rate", type=float, default=0.1, help="test split rate (default: 0.1)")
    parser.add_argument("--shuffle", action="store_true", help="shuffle records before splitting; default preserves source order")
    parser.add_argument("--seed", type=int, default=42, help="shuffle seed when --shuffle is used (default: 42)")
    parser.add_argument("--bidirectional", action="store_true", help="also match reversed tail,head pairs to the same relation")
    parser.add_argument("--strict-offsets", action="store_true", help="fail when head/tail offsets do not slice the given entity text")
    case = parser.add_mutually_exclusive_group()
    case.add_argument("--case-sensitive", dest="case_sensitive", action="store_true", help="match triples case-sensitively")
    case.add_argument("--case-insensitive", dest="case_sensitive", action="store_false", help="match triples case-insensitively")
    parser.set_defaults(case_sensitive=None)
    parser.add_argument("--encoding", default="utf-8", help="text/CSV/JSON encoding (default: utf-8)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        label_data(args)
    except DataPrepError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

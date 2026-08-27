#!/usr/bin/env python3
"""Validate local Tevatron JSONL, ranking, and qrels files.

This script performs static checks only. It does not import Tevatron, Torch,
Transformers, Hugging Face datasets, or model code, so it is safe for quick
preflight checks before expensive training, encoding, retrieval, or reranking.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


PASSAGE_LIST_KEYS = ("positive_passages", "negative_passages")
DOC_ID_KEYS = ("positive_document_ids", "negative_document_ids")
QUERY_ASSET_KEYS = ("query_image", "query_audio", "query_video")
DOC_ASSET_KEYS = ("image", "audio", "video")


class ValidationErrorCollector:
    def __init__(self, max_errors: int) -> None:
        self.max_errors = max_errors
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, line_number: int | str, message: str) -> None:
        if len(self.errors) < self.max_errors:
            self.errors.append(f"line {line_number}: {message}")

    def warn(self, line_number: int | str, message: str) -> None:
        if len(self.warnings) < self.max_errors:
            self.warnings.append(f"line {line_number}: {message}")

    @property
    def ok(self) -> bool:
        return not self.errors


def read_jsonl(path: Path, collector: ValidationErrorCollector) -> Iterable[tuple[int, dict[str, Any]]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    collector.warn(line_number, "blank line ignored")
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    collector.error(line_number, f"invalid JSON: {exc.msg} at column {exc.colno}")
                    continue
                if not isinstance(value, dict):
                    collector.error(line_number, "expected a JSON object")
                    continue
                yield line_number, value
    except OSError as exc:
        collector.error("file", f"cannot read {path}: {exc}")


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def is_string_list(value: Any, *, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(is_nonempty_string(item) for item in value)
    )


def has_any_value(row: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(row.get(key) not in (None, "") for key in keys)


def validate_optional_score(collector: ValidationErrorCollector, line_number: int, row: dict[str, Any]) -> None:
    if "score" in row and row["score"] is not None and not isinstance(row["score"], (int, float)):
        collector.warn(line_number, "score should be numeric when present")


def check_asset_value(
    collector: ValidationErrorCollector,
    line_number: int,
    field: str,
    value: Any,
    assets_root: Path | None,
) -> None:
    if value in (None, ""):
        return
    if field.endswith("audio") or field == "audio":
        if isinstance(value, dict):
            if "array" not in value:
                collector.warn(line_number, f"{field} object has no array key")
            return
        if not isinstance(value, str):
            collector.warn(line_number, f"{field} should be a .mp3 path string or an object with array")
            return
        if not value.endswith(".mp3"):
            collector.warn(line_number, f"{field} string does not end with .mp3")
    elif not isinstance(value, (str, dict)):
        collector.warn(line_number, f"{field} should be a path string or dataset asset object")
        return

    if isinstance(value, str):
        if assets_root is None:
            if field.endswith(("audio", "video")) or field in {"audio", "video"}:
                collector.warn(line_number, f"{field} path present but --assets-root was not provided")
            return
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = assets_root / candidate
        if not candidate.exists():
            collector.error(line_number, f"{field} asset does not exist: {value}")


def check_media_fields(
    collector: ValidationErrorCollector,
    line_number: int,
    row: dict[str, Any],
    fields: tuple[str, ...],
    assets_root: Path | None,
) -> None:
    for field in fields:
        if field in row:
            check_asset_value(collector, line_number, field, row.get(field), assets_root)


def validate_passage_object(
    collector: ValidationErrorCollector,
    line_number: int,
    passage: Any,
    field: str,
    index: int,
) -> None:
    if not isinstance(passage, dict):
        collector.error(line_number, f"{field}[{index}] must be an object")
        return
    if "text" not in passage or passage.get("text") is None:
        collector.error(line_number, f"{field}[{index}] missing text")
    elif not isinstance(passage.get("text"), str):
        collector.error(line_number, f"{field}[{index}].text must be a string")
    if "docid" not in passage:
        collector.warn(line_number, f"{field}[{index}] has no docid; joins and negative filtering may be harder")
    elif not is_nonempty_string(passage.get("docid")):
        collector.error(line_number, f"{field}[{index}].docid must be a non-empty string")
    if "title" in passage and passage.get("title") is not None and not isinstance(passage.get("title"), str):
        collector.error(line_number, f"{field}[{index}].title must be a string when present")
    validate_optional_score(collector, line_number, passage)


def load_corpus_ids(path: Path | None, collector: ValidationErrorCollector) -> set[str] | None:
    if path is None:
        return None
    ids: set[str] = set()
    for line_number, row in read_jsonl(path, collector):
        docid = row.get("docid")
        if not is_nonempty_string(docid):
            collector.error(line_number, "corpus row missing non-empty docid")
            continue
        if docid in ids:
            collector.warn(line_number, f"duplicate corpus docid {docid!r}")
        ids.add(docid)
    return ids


def validate_train_new(
    path: Path,
    collector: ValidationErrorCollector,
    corpus_ids: set[str] | None,
    train_group_size: int,
    assets_root: Path | None,
) -> Counter[str]:
    stats: Counter[str] = Counter()
    seen_qids: set[str] = set()
    expected_negatives = max(0, train_group_size - 1)
    for line_number, row in read_jsonl(path, collector):
        stats["rows"] += 1
        qid = row.get("query_id")
        if not is_nonempty_string(qid):
            collector.error(line_number, "missing non-empty query_id")
        elif qid in seen_qids:
            collector.warn(line_number, f"duplicate query_id {qid!r}")
        else:
            seen_qids.add(qid)

        if "query_text" not in row or row.get("query_text") in (None, ""):
            if not has_any_value(row, QUERY_ASSET_KEYS):
                collector.warn(line_number, "query_text is empty and no query-side asset field is present")
        elif not isinstance(row.get("query_text"), str):
            collector.error(line_number, "query_text must be a string when present")
        check_media_fields(collector, line_number, row, QUERY_ASSET_KEYS, assets_root)

        positives = row.get("positive_document_ids")
        negatives = row.get("negative_document_ids")
        if not is_string_list(positives, allow_empty=False):
            collector.error(line_number, "positive_document_ids must be a non-empty list of non-empty strings")
            positives = []
        if not is_string_list(negatives, allow_empty=True):
            collector.error(line_number, "negative_document_ids must be a list of non-empty strings")
            negatives = []

        positive_set = set(positives)
        negative_set = set(negatives)
        if positive_set & negative_set:
            collector.error(line_number, "positive_document_ids and negative_document_ids overlap")
        if len(negative_set) < expected_negatives:
            collector.warn(
                line_number,
                f"only {len(negative_set)} unique negatives; train_group_size={train_group_size} usually needs {expected_negatives}",
            )
        if corpus_ids is None:
            collector.warn(line_number, "no --corpus supplied; document IDs were not checked against corpus docids")
        else:
            missing = sorted((positive_set | negative_set) - corpus_ids)
            if missing:
                preview = ", ".join(missing[:5])
                collector.error(line_number, f"document IDs missing from corpus: {preview}")
    return stats


def validate_train_legacy(
    path: Path,
    collector: ValidationErrorCollector,
    train_group_size: int,
) -> Counter[str]:
    stats: Counter[str] = Counter()
    expected_negatives = max(0, train_group_size - 1)
    for line_number, row in read_jsonl(path, collector):
        stats["rows"] += 1
        if not is_nonempty_string(row.get("query")):
            collector.error(line_number, "missing non-empty query")
        for field in PASSAGE_LIST_KEYS:
            value = row.get(field)
            if not isinstance(value, list) or (field == "positive_passages" and not value):
                collector.error(line_number, f"{field} must be a {'non-empty ' if field == 'positive_passages' else ''}list")
                continue
            if field == "negative_passages" and len(value) < expected_negatives:
                collector.warn(
                    line_number,
                    f"only {len(value)} negatives; train_group_size={train_group_size} usually needs {expected_negatives}",
                )
            for index, passage in enumerate(value):
                validate_passage_object(collector, line_number, passage, field, index)
    return stats


def validate_corpus(path: Path, collector: ValidationErrorCollector, assets_root: Path | None) -> Counter[str]:
    stats: Counter[str] = Counter()
    seen_docids: set[str] = set()
    for line_number, row in read_jsonl(path, collector):
        stats["rows"] += 1
        docid = row.get("docid")
        if not is_nonempty_string(docid):
            collector.error(line_number, "missing non-empty docid")
        elif docid in seen_docids:
            collector.warn(line_number, f"duplicate docid {docid!r}")
        else:
            seen_docids.add(docid)
        text = row.get("text")
        if text in (None, ""):
            if not has_any_value(row, DOC_ASSET_KEYS):
                collector.warn(line_number, "text is empty and no document asset field is present")
        elif not isinstance(text, str):
            collector.error(line_number, "text must be a string when present")
        if "title" in row and row.get("title") is not None and not isinstance(row.get("title"), str):
            collector.error(line_number, "title must be a string when present")
        check_media_fields(collector, line_number, row, DOC_ASSET_KEYS, assets_root)
        validate_optional_score(collector, line_number, row)
    return stats


def validate_query(path: Path, collector: ValidationErrorCollector, assets_root: Path | None) -> Counter[str]:
    stats: Counter[str] = Counter()
    seen_qids: set[str] = set()
    for line_number, row in read_jsonl(path, collector):
        stats["rows"] += 1
        qid = row.get("query_id")
        if not is_nonempty_string(qid):
            collector.error(line_number, "missing non-empty query_id")
        elif qid in seen_qids:
            collector.warn(line_number, f"duplicate query_id {qid!r}")
        else:
            seen_qids.add(qid)
        query_text = row.get("query_text", row.get("query"))
        if query_text in (None, "") and not has_any_value(row, QUERY_ASSET_KEYS):
            collector.warn(line_number, "query text is empty and no query-side asset field is present")
        elif query_text is not None and not isinstance(query_text, str):
            collector.error(line_number, "query_text/query must be a string when present")
        check_media_fields(collector, line_number, row, QUERY_ASSET_KEYS, assets_root)
    return stats


def validate_rerank(path: Path, collector: ValidationErrorCollector) -> Counter[str]:
    stats: Counter[str] = Counter()
    for line_number, row in read_jsonl(path, collector):
        stats["rows"] += 1
        for field in ("query_id", "query", "docid", "title", "text"):
            if field not in row:
                collector.error(line_number, f"missing {field}")
            elif row[field] is None:
                collector.error(line_number, f"{field} must not be null")
            elif not isinstance(row[field], str):
                collector.error(line_number, f"{field} must be a string")
        validate_optional_score(collector, line_number, row)
    return stats


def parse_ranking_row(parts: list[str]) -> tuple[str, str, str]:
    if len(parts) == 3:
        qid, docid, score = parts
        return qid, docid, score
    if len(parts) == 4:
        qid, docid, _rank, score = parts
        if docid in {"0", "Q0"}:
            raise ValueError("four-column row looks like qrels, not ranking; expected qid docid rank score")
        return qid, docid, score
    if len(parts) >= 6:
        qid, _q0, docid, _rank, score, *_rest = parts
        return qid, docid, score
    raise ValueError(f"expected 3 ranking columns, 4 ranking columns, or at least 6 TREC columns, got {len(parts)}")


def validate_ranking(path: Path, collector: ValidationErrorCollector, corpus_ids: set[str] | None) -> Counter[str]:
    stats: Counter[str] = Counter()
    seen_qids: set[str] = set()
    closed_qids: set[str] = set()
    current_qid: str | None = None
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    collector.warn(line_number, "blank line ignored")
                    continue
                stats["rows"] += 1
                parts = line.split()
                try:
                    qid, docid, score = parse_ranking_row(parts)
                except ValueError as exc:
                    collector.error(line_number, str(exc))
                    continue
                if not qid or not docid:
                    collector.error(line_number, "qid and docid must be non-empty")
                try:
                    float(score)
                except ValueError:
                    collector.error(line_number, f"score is not numeric: {score!r}")
                if current_qid is None:
                    current_qid = qid
                elif qid != current_qid:
                    closed_qids.add(current_qid)
                    current_qid = qid
                if qid in closed_qids:
                    collector.warn(line_number, f"query {qid!r} is not contiguous; converters restart rank on each block")
                seen_qids.add(qid)
                if corpus_ids is not None and docid not in corpus_ids:
                    collector.error(line_number, f"docid {docid!r} missing from corpus")
    except OSError as exc:
        collector.error("file", f"cannot read {path}: {exc}")
    stats["queries"] = len(seen_qids)
    return stats


def validate_qrels(path: Path, collector: ValidationErrorCollector, corpus_ids: set[str] | None) -> Counter[str]:
    stats: Counter[str] = Counter()
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    collector.warn(line_number, "blank line ignored")
                    continue
                stats["rows"] += 1
                parts = line.split()
                if len(parts) != 4:
                    collector.error(line_number, f"qrels must have 4 columns: qid 0 docid relevance; got {len(parts)}")
                    continue
                qid, iteration, docid, relevance = parts
                if not qid or not docid:
                    collector.error(line_number, "qid and docid must be non-empty")
                if iteration != "0":
                    collector.warn(line_number, f"qrels second column is usually 0, got {iteration!r}")
                try:
                    float(relevance)
                except ValueError:
                    collector.error(line_number, f"relevance is not numeric: {relevance!r}")
                if corpus_ids is not None and docid not in corpus_ids:
                    collector.error(line_number, f"docid {docid!r} missing from corpus")
    except OSError as exc:
        collector.error("file", f"cannot read {path}: {exc}")
    return stats


def infer_train_kind(path: Path, collector: ValidationErrorCollector) -> str | None:
    for _line_number, row in read_jsonl(path, collector):
        if all(key in row for key in DOC_ID_KEYS):
            return "train-new"
        if all(key in row for key in PASSAGE_LIST_KEYS):
            return "train-legacy"
        return None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kind",
        choices=["train-new", "train-legacy", "train", "corpus", "query", "rerank", "ranking", "qrels"],
        required=True,
    )
    parser.add_argument("--input", required=True, type=Path, help="JSONL, ranking, or qrels file to validate")
    parser.add_argument("--corpus", type=Path, help="Optional corpus JSONL for document-ID checks")
    parser.add_argument("--assets-root", type=Path, help="Optional root used to verify relative audio/video/image asset paths")
    parser.add_argument("--train-group-size", type=int, default=8, help="Expected Tevatron train_group_size for negative-count warnings")
    parser.add_argument("--max-errors", type=int, default=25, help="Maximum errors and warnings to print")
    args = parser.parse_args(argv)

    collector = ValidationErrorCollector(max_errors=args.max_errors)
    kind = args.kind
    if kind == "train":
        inferred = infer_train_kind(args.input, collector)
        if inferred is None:
            collector.error(1, "could not infer train format; expected document ID fields or passage lists")
        else:
            kind = inferred

    needs_corpus_ids = kind in {"train-new", "ranking", "qrels"} and args.corpus is not None
    corpus_ids = load_corpus_ids(args.corpus, collector) if needs_corpus_ids else None

    if kind == "train-new":
        stats = validate_train_new(args.input, collector, corpus_ids, args.train_group_size, args.assets_root)
    elif kind == "train-legacy":
        stats = validate_train_legacy(args.input, collector, args.train_group_size)
    elif kind == "corpus":
        stats = validate_corpus(args.input, collector, args.assets_root)
    elif kind == "query":
        stats = validate_query(args.input, collector, args.assets_root)
    elif kind == "rerank":
        stats = validate_rerank(args.input, collector)
    elif kind == "ranking":
        stats = validate_ranking(args.input, collector, corpus_ids)
    elif kind == "qrels":
        stats = validate_qrels(args.input, collector, corpus_ids)
    else:
        stats = Counter()

    for message in collector.errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in collector.warnings:
        print(f"WARNING: {message}", file=sys.stderr)

    row_count = stats.get("rows", 0)
    if collector.ok:
        print(f"OK: {args.input} passed {kind} validation ({row_count} rows)")
        return 0
    print(f"FAILED: {args.input} failed {kind} validation ({row_count} rows, {len(collector.errors)} errors)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

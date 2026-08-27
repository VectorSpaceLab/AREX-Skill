#!/usr/bin/env python3
"""Prepare Tevatron reranker JSONL input from local query/corpus/run fixtures.

This bundled helper is adapted from Tevatron's rerank-input formatting utility,
but it avoids external dataset downloads and uses explicit run-file parsing for
small local fixtures. It writes one JSON object per query-document pair with the
fields expected by tevatron.reranker.driver.rerank.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


JsonRecord = Dict[str, Any]
RunRows = Dict[str, List[Tuple[str, float]]]


def load_jsonl_map(path: Path, id_fields: Iterable[str]) -> Dict[str, JsonRecord]:
    records: Dict[str, JsonRecord] = {}
    id_field_list = list(id_fields)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {error}") from error
            if not isinstance(record, dict):
                raise SystemExit(f"{path}:{line_number}: expected a JSON object")
            record_id = first_present(record, id_field_list)
            if record_id is None:
                raise SystemExit(f"{path}:{line_number}: missing id field from {id_field_list}")
            records[str(record_id)] = record
    return records


def first_present(record: JsonRecord, fields: Iterable[str]) -> Any:
    for field in fields:
        value = record.get(field)
        if value is not None:
            return value
    return None


def text_from(record: JsonRecord, fields: Iterable[str], default: str = "") -> str:
    value = first_present(record, fields)
    if value is None:
        return default
    return str(value)


def parse_run_line(line: str, line_number: int, path: Path) -> Tuple[str, str, float]:
    parts = line.strip().split()
    if len(parts) == 3:
        qid, docid, score = parts
    elif len(parts) == 4:
        qid, docid, _rank, score = parts
    elif len(parts) >= 6:
        qid, _q0, docid, _rank, score, *_rest = parts
    else:
        raise SystemExit(
            f"{path}:{line_number}: expected 3, 4, or >=6 whitespace-separated run columns; got {len(parts)}"
        )
    try:
        parsed_score = float(score)
    except ValueError as error:
        raise SystemExit(f"{path}:{line_number}: score is not numeric: {score!r}") from error
    return qid, docid, parsed_score


def read_run(path: Path, dedupe: bool) -> RunRows:
    results: RunRows = {}
    seen = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            qid, docid, score = parse_run_line(line, line_number, path)
            key = (qid, docid)
            if dedupe and key in seen:
                continue
            seen.add(key)
            results.setdefault(qid, []).append((docid, score))
    return results


def build_rows(
    queries: Dict[str, JsonRecord],
    corpus: Dict[str, JsonRecord],
    run: RunRows,
    depth: int,
    strict: bool,
) -> Tuple[List[JsonRecord], int, int]:
    rows: List[JsonRecord] = []
    missing_queries = 0
    missing_docs = 0
    for qid, doc_scores in run.items():
        query_record = queries.get(qid)
        if query_record is None:
            missing_queries += 1
            if strict:
                raise SystemExit(f"run references missing query id {qid!r}")
            continue
        query_text = text_from(query_record, ["query", "text", "contents"])
        if not query_text and strict:
            raise SystemExit(f"query id {qid!r} has no query/text/contents value")
        for docid, score in doc_scores[:depth]:
            doc_record = corpus.get(docid)
            if doc_record is None:
                missing_docs += 1
                if strict:
                    raise SystemExit(f"run references missing doc id {docid!r} for query {qid!r}")
                continue
            doc_text = text_from(doc_record, ["text", "contents", "body"])
            if not doc_text and strict:
                raise SystemExit(f"doc id {docid!r} has no text/contents/body value")
            rows.append(
                {
                    "query_id": qid,
                    "query": query_text,
                    "docid": docid,
                    "title": text_from(doc_record, ["title"], default=""),
                    "text": doc_text,
                    "score": score,
                }
            )
    return rows, missing_queries, missing_docs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", required=True, type=Path, help="Query JSONL with query_id/qid/id and query/text fields.")
    parser.add_argument("--corpus", required=True, type=Path, help="Corpus JSONL with docid/doc_id/pid/id and text/contents fields.")
    parser.add_argument("--run", required=True, type=Path, help="First-stage retrieval run file.")
    parser.add_argument("--output", required=True, type=Path, help="Output reranker JSONL path.")
    parser.add_argument("--depth", type=int, default=1000, help="Maximum candidates per query to keep.")
    parser.add_argument("--strict", action="store_true", help="Fail on missing query/doc ids or empty text instead of skipping/allowing them.")
    parser.add_argument("--dedupe", action="store_true", help="Keep only the first occurrence of each query-document pair in the run file.")
    args = parser.parse_args()

    if args.depth < 1:
        raise SystemExit("--depth must be at least 1")

    queries = load_jsonl_map(args.queries, ["query_id", "qid", "id"])
    corpus = load_jsonl_map(args.corpus, ["docid", "doc_id", "pid", "id"])
    run = read_run(args.run, dedupe=args.dedupe)
    rows, missing_queries, missing_docs = build_rows(queries, corpus, run, args.depth, args.strict)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        f"wrote {len(rows)} rows to {args.output} "
        f"(queries={len(queries)}, docs={len(corpus)}, run_queries={len(run)}, "
        f"missing_queries={missing_queries}, missing_docs={missing_docs})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

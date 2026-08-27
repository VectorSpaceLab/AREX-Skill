#!/usr/bin/env python3
"""Convert DeepKE MT5/CCKS prediction JSONL into result JSONL with parsed ``kg`` triples.

The source DeepKE helper reads one source JSON object and one prediction JSON
object per line, copies the generated ``output`` text, parses parenthesized
triples, and writes a JSONL result. This standalone version adds validation,
JSON-array input support, row-count checks, and clearer errors while preserving
that operating contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

TRIPLE_RE = re.compile(r"\(([^()]*)\)")
DEFAULT_PREFIXES = (
    "输入中包含的关系三元组是：",
    "输入中包含的关系三元组是:",
    "关系三元组是：",
    "关系三元组是:",
)


class ConvertError(Exception):
    """Raised for input or conversion errors."""


def load_json_records(path: Path) -> List[Dict[str, Any]]:
    """Read JSONL or a JSON array/object from *path*."""
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    if text[0] == "[":
        data = json.loads(text)
        if not isinstance(data, list):
            raise ConvertError(f"{path}: top-level JSON array expected")
        records = data
    elif text[0] == "{" and "\n" not in text:
        records = [json.loads(text)]
    else:
        records = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ConvertError(f"{path}:{line_no}: invalid JSONL row: {exc}") from exc
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ConvertError(f"{path}: record {index} is {type(record).__name__}, expected object")
    return records  # type: ignore[return-value]


def strip_known_prefix(text: str, extra_prefixes: Sequence[str]) -> str:
    value = text.strip()
    for prefix in (*DEFAULT_PREFIXES, *extra_prefixes):
        if value.startswith(prefix):
            return value[len(prefix) :].strip()
    return value


def parse_triples(text: str, *, allow_chinese_comma: bool = False) -> List[List[str]]:
    """Parse parenthesized triples from a generated text string.

    The parser is intentionally conservative and mirrors DeepKE's source helper:
    triples are represented as ``(head, relation, tail)``. Commas inside entity
    names remain ambiguous and should be solved by changing the generation
    format or by writing a task-specific parser.
    """
    triples: List[List[str]] = []
    delimiter = r"[,，]" if allow_chinese_comma else r"," 
    for match in TRIPLE_RE.finditer(text):
        parts = [item.strip().strip("'\"") for item in re.split(delimiter, match.group(1))]
        if len(parts) < 3:
            continue
        head, relation = parts[0], parts[1]
        tail = ",".join(parts[2:]).strip()
        if head and relation and tail:
            triples.append([head, relation, tail])
    return triples


def convert_records(
    sources: Sequence[Dict[str, Any]],
    predictions: Sequence[Dict[str, Any]],
    *,
    prediction_field: str,
    output_field: str,
    kg_field: str,
    extra_prefixes: Sequence[str],
    allow_chinese_comma: bool,
    strict_length: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    if strict_length and len(sources) != len(predictions):
        raise ConvertError(f"row count mismatch: {len(sources)} source rows vs {len(predictions)} prediction rows")
    n = min(len(sources), len(predictions))
    output: List[Dict[str, Any]] = []
    stats = {"source_rows": len(sources), "prediction_rows": len(predictions), "written_rows": n, "empty_kg_rows": 0}
    for index in range(n):
        source = dict(sources[index])
        pred = predictions[index]
        if prediction_field not in pred:
            raise ConvertError(f"prediction row {index}: missing field {prediction_field!r}")
        raw = pred[prediction_field]
        if not isinstance(raw, str):
            raw = json.dumps(raw, ensure_ascii=False)
        cleaned = strip_known_prefix(raw, extra_prefixes)
        kg = parse_triples(cleaned, allow_chinese_comma=allow_chinese_comma)
        if not kg:
            stats["empty_kg_rows"] += 1
        source[output_field] = cleaned
        source[kg_field] = kg
        output.append(source)
    return output, stats


def write_jsonl(records: Iterable[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert DeepKE MT5/CCKS prediction output strings into JSONL records with parsed kg triples.")
    parser.add_argument("--src-path", required=True, help="source input JSONL/JSON array, e.g. data/valid.json")
    parser.add_argument("--pred-path", required=True, help="prediction JSONL/JSON array, e.g. output/test_preds.json")
    parser.add_argument("--tgt-path", required=True, help="output JSONL path")
    parser.add_argument("--prediction-field", default="output", help="field in prediction records that contains generated text (default: output)")
    parser.add_argument("--output-field", default="output", help="field to write cleaned generated text into (default: output)")
    parser.add_argument("--kg-field", default="kg", help="field to write parsed triples into (default: kg)")
    parser.add_argument("--strip-prefix", action="append", default=[], help="additional generated-text prefix to strip; may be repeated")
    parser.add_argument("--allow-chinese-comma", action="store_true", help="also split triples on the Chinese comma '，'")
    parser.add_argument("--strict-length", action="store_true", help="fail if source and prediction row counts differ")
    parser.add_argument("--stats", action="store_true", help="print conversion stats as JSON to stderr")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        sources = load_json_records(Path(args.src_path))
        predictions = load_json_records(Path(args.pred_path))
        records, stats = convert_records(
            sources,
            predictions,
            prediction_field=args.prediction_field,
            output_field=args.output_field,
            kg_field=args.kg_field,
            extra_prefixes=args.strip_prefix,
            allow_chinese_comma=args.allow_chinese_comma,
            strict_length=args.strict_length,
        )
        write_jsonl(records, Path(args.tgt_path))
        if args.stats:
            print(json.dumps(stats, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    except (OSError, json.JSONDecodeError, ConvertError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

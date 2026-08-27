#!/usr/bin/env python3
"""Summarize labeled pair-score files for text2vec evaluation.

Reads CSV/TSV or JSONL rows with a gold label and a predicted score, computes
Spearman and Pearson correlation, and writes a JSON summary. This helper does
not load models and does not download benchmark data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

MetricFn = Callable[[Sequence[float], Sequence[float]], Optional[float]]


def _jsonable_float(value: object) -> Optional[float]:
    """Convert metric outputs to JSON-safe finite floats or None."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _pearson_fallback(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = math.fsum(xs) / len(xs)
    mean_y = math.fsum(ys) / len(ys)
    centered_x = [x - mean_x for x in xs]
    centered_y = [y - mean_y for y in ys]
    denom = math.sqrt(
        math.fsum(v * v for v in centered_x) * math.fsum(v * v for v in centered_y)
    )
    if denom == 0.0:
        return None
    return math.fsum(a * b for a, b in zip(centered_x, centered_y)) / denom


def _rankdata(values: Sequence[float]) -> List[float]:
    """Average-tie ranks compatible with Spearman correlation."""
    indexed = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        average_rank = (i + 1 + j) / 2.0  # 1-based average rank over [i + 1, j]
        for k in range(i, j):
            original_index = indexed[k][0]
            ranks[original_index] = average_rank
        i = j
    return ranks


def _spearman_fallback(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    return _pearson_fallback(_rankdata(xs), _rankdata(ys))


def _load_metric_backend() -> Tuple[str, MetricFn, MetricFn]:
    """Prefer scipy, then text2vec utilities, then local deterministic fallback."""
    try:
        from scipy.stats import pearsonr as scipy_pearsonr  # type: ignore
        from scipy.stats import spearmanr as scipy_spearmanr  # type: ignore

        def scipy_spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
            return _jsonable_float(scipy_spearmanr(xs, ys).correlation)

        def scipy_pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
            return _jsonable_float(scipy_pearsonr(xs, ys)[0])

        return "scipy", scipy_spearman, scipy_pearson
    except Exception:
        pass

    try:
        from text2vec.utils.stats_util import compute_pearsonr, compute_spearmanr  # type: ignore

        def text2vec_spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
            return _jsonable_float(compute_spearmanr(xs, ys))

        def text2vec_pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
            return _jsonable_float(compute_pearsonr(xs, ys))

        return "text2vec", text2vec_spearman, text2vec_pearson
    except Exception:
        pass

    def fallback_spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
        return _jsonable_float(_spearman_fallback(xs, ys))

    def fallback_pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
        return _jsonable_float(_pearson_fallback(xs, ys))

    return "fallback", fallback_spearman, fallback_pearson


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson", ".jl", ".json"}:
        return "jsonl"
    if suffix in {".csv", ".tsv"}:
        return "csv"

    with path.open("r", encoding="utf-8-sig") as handle:
        while True:
            char = handle.read(1)
            if not char:
                return "csv"
            if not char.isspace():
                return "jsonl" if char in "[{" else "csv"


def _iter_csv_records(path: Path) -> Iterator[Dict[str, object]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        if not sample:
            return
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        except csv.Error:
            dialect = csv.excel_tab if path.suffix.lower() == ".tsv" else csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        if reader.fieldnames is None:
            raise ValueError("CSV input must include a header row")
        reader.fieldnames = [name.strip() if isinstance(name, str) else name for name in reader.fieldnames]
        for row in reader:
            yield {key.strip() if isinstance(key, str) else key: value for key, value in row.items()}


def _iter_jsonl_records(path: Path) -> Iterator[Dict[str, object]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        stripped_lines = [(idx, line.strip()) for idx, line in enumerate(handle, start=1) if line.strip()]

    if not stripped_lines:
        return

    # Accept a single JSON object/array as a convenience, while keeping JSONL as default.
    if len(stripped_lines) == 1 and stripped_lines[0][1][0] in "[{":
        line_no, text = stripped_lines[0]
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at line {line_no}: {exc}") from exc
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("JSON array records must be objects")
                yield item
            return
        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                for item in data["data"]:
                    if not isinstance(item, dict):
                        raise ValueError("JSON data records must be objects")
                    yield item
            else:
                yield data
            return
        raise ValueError("JSON input must be an object, array of objects, or JSONL objects")

    for line_no, text in stripped_lines:
        try:
            item = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"JSONL record at line {line_no} must be an object")
        yield item


def _iter_records(path: Path, input_format: str) -> Iterator[Dict[str, object]]:
    if input_format == "csv":
        yield from _iter_csv_records(path)
    elif input_format == "jsonl":
        yield from _iter_jsonl_records(path)
    else:
        raise ValueError(f"Unsupported input format: {input_format}")


def _parse_number(record: Dict[str, object], column: str) -> float:
    if column not in record:
        raise ValueError(f"missing column {column!r}")
    raw_value = record[column]
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
    if raw_value in (None, ""):
        raise ValueError(f"empty value in column {column!r}")
    try:
        number = float(raw_value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"nonnumeric value in column {column!r}: {raw_value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"non-finite value in column {column!r}: {raw_value!r}")
    return number


def _collect_pairs(
    records: Iterable[Dict[str, object]], label_column: str, score_column: str
) -> Tuple[List[float], List[float], int, List[Dict[str, object]]]:
    labels: List[float] = []
    scores: List[float] = []
    skipped_examples: List[Dict[str, object]] = []
    total_rows = 0

    for row_number, record in enumerate(records, start=1):
        total_rows += 1
        try:
            label = _parse_number(record, label_column)
            score = _parse_number(record, score_column)
        except ValueError as exc:
            if len(skipped_examples) < 10:
                skipped_examples.append({"row": row_number, "reason": str(exc)})
            continue
        labels.append(label)
        scores.append(score)

    return labels, scores, total_rows, skipped_examples


def _metric_value(name: str, fn: MetricFn, labels: Sequence[float], scores: Sequence[float], warnings: List[str]) -> Optional[float]:
    try:
        value = fn(labels, scores)
    except Exception as exc:  # pragma: no cover - defensive for external backends
        warnings.append(f"{name} computation failed: {exc}")
        return None
    if value is None:
        warnings.append(f"{name} is undefined for the valid rows")
    return value


def summarize_file(input_file: Path, label_column: str, score_column: str) -> Dict[str, object]:
    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    input_format = _detect_format(input_file)
    labels, scores, total_rows, skipped_examples = _collect_pairs(
        _iter_records(input_file, input_format), label_column, score_column
    )

    backend_name, spearman_fn, pearson_fn = _load_metric_backend()
    warnings: List[str] = []
    skipped_rows = total_rows - len(labels)
    if skipped_rows:
        warnings.append(f"Skipped {skipped_rows} malformed row(s)")

    spearman: Optional[float] = None
    pearson: Optional[float] = None
    if len(labels) < 2:
        warnings.append("Need at least two valid rows to compute correlation")
    else:
        spearman = _metric_value("Spearman", spearman_fn, labels, scores, warnings)
        pearson = _metric_value("Pearson", pearson_fn, labels, scores, warnings)

    summary: Dict[str, object] = {
        "input_file": str(input_file),
        "input_format": input_format,
        "label_column": label_column,
        "score_column": score_column,
        "metric_backend": backend_name,
        "num_rows": total_rows,
        "num_valid_rows": len(labels),
        "num_skipped_rows": skipped_rows,
        "spearman": _jsonable_float(spearman),
        "pearson": _jsonable_float(pearson),
        "warnings": warnings,
        "skipped_examples": skipped_examples,
    }
    if labels:
        summary.update(
            {
                "label_min": min(labels),
                "label_max": max(labels),
                "score_min": min(scores),
                "score_max": max(scores),
            }
        )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute Spearman/Pearson for a CSV/JSONL file with gold labels and predicted scores."
    )
    parser.add_argument("--input-file", required=True, help="CSV/TSV/JSONL file to read.")
    parser.add_argument("--label-column", default="label", help="Gold label column/key name. Default: label.")
    parser.add_argument("--score-column", default="score", help="Predicted score column/key name. Default: score.")
    parser.add_argument("--output-file", required=True, help="JSON summary file to write.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_file = Path(args.input_file).expanduser()
    output_file = Path(args.output_file).expanduser()

    try:
        summary = summarize_file(input_file, args.label_column, args.score_column)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"Wrote summary to {output_file}")
    if summary.get("num_valid_rows", 0) < 2 or summary.get("spearman") is None or summary.get("pearson") is None:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

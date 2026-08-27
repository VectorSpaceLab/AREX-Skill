#!/usr/bin/env python3
"""Compute ClinVar ROC AUC from SaProt zero-shot CSV logs using explicit paths."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


Key = Tuple[str, str]


class ClinVarAucError(RuntimeError):
    """Raised for validation errors that should stop benchmark aggregation."""


def parse_float(value: Any, field_name: str, source: str) -> float:
    try:
        number = float(str(value).strip())
    except Exception as exc:
        raise ClinVarAucError(f"invalid numeric value for {field_name} in {source}: {value!r}") from exc
    if math.isnan(number):
        raise ClinVarAucError(f"NaN value for {field_name} in {source}")
    return number


def require_columns(fieldnames: Sequence[str] | None, required: Iterable[str], source: str) -> None:
    available = set(fieldnames or [])
    missing = [column for column in required if column not in available]
    if missing:
        raise ClinVarAucError(f"{source} missing required columns: {', '.join(missing)}")


def read_csv_rows(path: Path, required_columns: Sequence[str]) -> List[Dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            require_columns(reader.fieldnames, required_columns, str(path))
            return list(reader)
    except ClinVarAucError:
        raise
    except FileNotFoundError as exc:
        raise ClinVarAucError(f"file not found: {path}") from exc
    except OSError as exc:
        raise ClinVarAucError(f"could not read {path}: {exc}") from exc


def deduplicate_values(
    rows: Iterable[Tuple[Key, float, str]],
    value_name: str,
    allow_conflicting: bool,
    duplicate_keep: str,
) -> Tuple[Dict[Key, float], Dict[str, Any]]:
    values: Dict[Key, float] = {}
    sources: Dict[Key, str] = {}
    exact_duplicates = 0
    conflicting_duplicates: List[Dict[str, Any]] = []

    for key, value, source in rows:
        if key not in values:
            values[key] = value
            sources[key] = source
            continue
        if values[key] == value:
            exact_duplicates += 1
            continue
        conflict = {
            "protein_name": key[0],
            "mutations": key[1],
            "first_value": values[key],
            "new_value": value,
            "first_source": sources[key],
            "new_source": source,
        }
        conflicting_duplicates.append(conflict)
        if allow_conflicting and duplicate_keep == "last":
            values[key] = value
            sources[key] = source

    if conflicting_duplicates and not allow_conflicting:
        preview = "; ".join(
            f"{item['protein_name']} {item['mutations']} ({item['first_value']} vs {item['new_value']})"
            for item in conflicting_duplicates[:5]
        )
        raise ClinVarAucError(
            f"conflicting duplicate {value_name} rows found; use --allow-conflicting-duplicates "
            f"with --duplicate-keep if intentional: {preview}"
        )

    return values, {
        "exact_duplicates_dropped": exact_duplicates,
        "conflicting_duplicates": len(conflicting_duplicates),
        "duplicate_keep": duplicate_keep,
    }


def load_prediction_logs(
    log_dir: Path,
    protein_col: str,
    mutation_col: str,
    score_col: str,
    allow_conflicting: bool,
    duplicate_keep: str,
) -> Tuple[Dict[Key, float], Dict[str, Any]]:
    if not log_dir.exists() or not log_dir.is_dir():
        raise ClinVarAucError(f"log directory does not exist or is not a directory: {log_dir}")
    csv_paths = sorted(path for path in log_dir.glob("*.csv") if path.is_file())
    if not csv_paths:
        raise ClinVarAucError(f"no CSV log files found in {log_dir}")

    parsed_rows: List[Tuple[Key, float, str]] = []
    for path in csv_paths:
        rows = read_csv_rows(path, [protein_col, mutation_col, score_col])
        for row_number, row in enumerate(rows, start=2):
            protein = (row.get(protein_col) or "").strip()
            mutation = (row.get(mutation_col) or "").strip()
            if not protein or not mutation:
                raise ClinVarAucError(f"empty protein/mutation key in {path}:{row_number}")
            score = parse_float(row.get(score_col), score_col, f"{path}:{row_number}")
            parsed_rows.append(((protein, mutation), score, f"{path}:{row_number}"))

    predictions, duplicate_report = deduplicate_values(
        parsed_rows,
        "prediction",
        allow_conflicting=allow_conflicting,
        duplicate_keep=duplicate_keep,
    )
    report = {
        "log_files": [str(path) for path in csv_paths],
        "raw_prediction_rows": len(parsed_rows),
        "unique_prediction_rows": len(predictions),
        **duplicate_report,
    }
    return predictions, report


def load_labels(
    labels_csv: Path,
    protein_col: str,
    mutation_col: str,
    label_col: str,
    allow_conflicting: bool,
    duplicate_keep: str,
) -> Tuple[Dict[Key, float], List[Key], Dict[str, Any]]:
    rows = read_csv_rows(labels_csv, [protein_col, mutation_col, label_col])
    parsed_rows: List[Tuple[Key, float, str]] = []
    ordered_keys: List[Key] = []
    for row_number, row in enumerate(rows, start=2):
        protein = (row.get(protein_col) or "").strip()
        mutation = (row.get(mutation_col) or "").strip()
        if not protein or not mutation:
            raise ClinVarAucError(f"empty protein/mutation key in {labels_csv}:{row_number}")
        label = parse_float(row.get(label_col), label_col, f"{labels_csv}:{row_number}")
        key = (protein, mutation)
        parsed_rows.append((key, label, f"{labels_csv}:{row_number}"))
        ordered_keys.append(key)

    labels, duplicate_report = deduplicate_values(
        parsed_rows,
        "label",
        allow_conflicting=allow_conflicting,
        duplicate_keep=duplicate_keep,
    )
    seen = set()
    unique_ordered_keys = []
    for key in ordered_keys:
        if key not in seen:
            seen.add(key)
            unique_ordered_keys.append(key)
    report = {
        "raw_label_rows": len(parsed_rows),
        "unique_label_rows": len(labels),
        **duplicate_report,
    }
    return labels, unique_ordered_keys, report


def roc_auc_score(labels: Sequence[int], scores: Sequence[float]) -> float:
    if len(labels) != len(scores):
        raise ClinVarAucError("labels and scores must have the same length")
    positives = sum(1 for label in labels if label == 1)
    negatives = sum(1 for label in labels if label == 0)
    if positives == 0 or negatives == 0:
        raise ClinVarAucError("ROC AUC requires at least one positive and one negative label")

    pairs = sorted(zip(scores, labels), key=lambda item: item[0])
    rank_sum_positive = 0.0
    rank = 1
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and pairs[end][0] == pairs[index][0]:
            end += 1
        average_rank = (rank + rank + (end - index) - 1) / 2.0
        positives_in_group = sum(1 for _, label in pairs[index:end] if label == 1)
        rank_sum_positive += positives_in_group * average_rank
        rank += end - index
        index = end

    return (rank_sum_positive - positives * (positives + 1) / 2.0) / (positives * negatives)


def build_merged_rows(
    predictions: Dict[Key, float],
    labels: Dict[Key, float],
    ordered_label_keys: Sequence[Key],
    allow_missing_predictions: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    merged_rows: List[Dict[str, Any]] = []
    missing_predictions: List[Key] = []
    ambiguous_labels = 0
    skipped_non_binary = 0

    for key in ordered_label_keys:
        label = labels[key]
        if label == 0.5:
            ambiguous_labels += 1
            continue
        if label not in {0.0, 1.0}:
            skipped_non_binary += 1
            continue
        if key not in predictions:
            missing_predictions.append(key)
            if allow_missing_predictions:
                continue
            continue
        merged_rows.append(
            {
                "protein_name": key[0],
                "mutations": key[1],
                "ClinVar_labels": int(label),
                "evol_indices": predictions[key],
            }
        )

    if missing_predictions and not allow_missing_predictions:
        preview = "; ".join(f"{protein} {mutation}" for protein, mutation in missing_predictions[:10])
        raise ClinVarAucError(
            f"missing predictions for {len(missing_predictions)} non-ambiguous label rows; "
            f"use --allow-missing-predictions to skip them if intentional: {preview}"
        )

    report = {
        "ambiguous_0_5_labels_skipped": ambiguous_labels,
        "non_binary_labels_skipped": skipped_non_binary,
        "missing_predictions": len(missing_predictions),
        "merged_rows": len(merged_rows),
    }
    return merged_rows, report


def write_merged_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["protein_name", "mutations", "ClinVar_labels", "evol_indices"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute ClinVar ROC AUC from SaProt zero-shot prediction CSV logs.")
    parser.add_argument("--log-dir", required=True, help="Directory containing SaProt ClinVar prediction CSV logs.")
    parser.add_argument("--labels-csv", required=True, help="ClinVar labels CSV path.")
    parser.add_argument("--protein-name", default="protein_name", help="Protein-name column used in logs and labels.")
    parser.add_argument("--mutation-col", default="mutations", help="Mutation column used in logs and labels.")
    parser.add_argument("--score-col", default="evol_indices", help="Prediction score column in log CSVs.")
    parser.add_argument("--label-col", default="ClinVar_labels", help="Binary/ambiguous label column in labels CSV.")
    parser.add_argument(
        "--allow-conflicting-duplicates",
        action="store_true",
        help="Allow conflicting duplicate keys and resolve them with --duplicate-keep.",
    )
    parser.add_argument(
        "--duplicate-keep",
        choices=("first", "last"),
        default="first",
        help="Resolution policy when --allow-conflicting-duplicates is set.",
    )
    parser.add_argument(
        "--allow-missing-predictions",
        action="store_true",
        help="Skip label rows without predictions instead of failing.",
    )
    parser.add_argument("--output-csv", help="Optional path for the merged rows used in AUC computation.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of human-readable text.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        predictions, prediction_report = load_prediction_logs(
            Path(args.log_dir).expanduser(),
            protein_col=args.protein_name,
            mutation_col=args.mutation_col,
            score_col=args.score_col,
            allow_conflicting=args.allow_conflicting_duplicates,
            duplicate_keep=args.duplicate_keep,
        )
        labels, ordered_label_keys, label_report = load_labels(
            Path(args.labels_csv).expanduser(),
            protein_col=args.protein_name,
            mutation_col=args.mutation_col,
            label_col=args.label_col,
            allow_conflicting=args.allow_conflicting_duplicates,
            duplicate_keep=args.duplicate_keep,
        )
        merged_rows, merge_report = build_merged_rows(
            predictions,
            labels,
            ordered_label_keys,
            allow_missing_predictions=args.allow_missing_predictions,
        )
        auc = roc_auc_score(
            [int(row["ClinVar_labels"]) for row in merged_rows],
            [float(row["evol_indices"]) for row in merged_rows],
        )
        if args.output_csv:
            write_merged_csv(Path(args.output_csv).expanduser(), merged_rows)

        report = {
            "ok": True,
            "auc": auc,
            "log_dir": str(Path(args.log_dir).expanduser()),
            "labels_csv": str(Path(args.labels_csv).expanduser()),
            "output_csv": args.output_csv,
            "predictions": prediction_report,
            "labels": label_report,
            "merge": merge_report,
        }
    except ClinVarAucError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ClinVar ROC AUC: {auc:.6f}")
        print(f"Prediction rows: {prediction_report['unique_prediction_rows']} unique from {len(prediction_report['log_files'])} files")
        print(f"Label rows: {label_report['unique_label_rows']} unique")
        print(f"Merged rows used: {merge_report['merged_rows']}")
        print(f"Ambiguous 0.5 labels skipped: {merge_report['ambiguous_0_5_labels_skipped']}")
        if merge_report["missing_predictions"]:
            print(f"Missing predictions skipped: {merge_report['missing_predictions']}")
        if args.output_csv:
            print(f"Merged CSV: {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Scan VLMEvalKit prediction/evaluation outputs for API-style failures.

This helper is intentionally self-contained: it does not import vlmeval and can
inspect copied output directories that contain common CSV/TSV/JSON/XLSX files.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

FAIL_MSG = "Failed to obtain answer via API."
EVAL_ID_RE = re.compile(r"^(T\d{8}[-_]\d{6}|T\d{8}_G[0-9a-fA-F]+)$")
PRED_SUFFIXES = (".xlsx", ".tsv", ".json")
EVAL_SUFFIXES = (".xlsx", ".csv", ".tsv", ".json")
TEMP_MARKERS = ("_checkpoint", "_PREV", "_structs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-root",
        type=Path,
        required=True,
        help="Model output root or one eval-id run directory to scan.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Model name used in result filenames. Defaults to model-root name, or parent name for eval-id dirs.",
    )
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=None,
        help="Dataset names to scan. If omitted, datasets are inferred from prediction files.",
    )
    parser.add_argument(
        "--pred-format",
        choices=["auto", "xlsx", "tsv", "json"],
        default="auto",
        help="Prediction format to look for when datasets are explicit.",
    )
    parser.add_argument(
        "--fail-substring",
        default=FAIL_MSG,
        help="Substring that marks failed inference/evaluation rows.",
    )
    parser.add_argument(
        "--include-run-dirs",
        action="store_true",
        help="Also scan direct child directories that contain status.json.",
    )
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="Report missing prediction files for explicit --datasets.",
    )
    parser.add_argument(
        "--fail-on-detected",
        action="store_true",
        help="Exit with code 2 when failures or requested missing predictions are detected.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    return parser.parse_args()


def infer_model_name(root: Path, supplied: str | None) -> str:
    if supplied:
        return supplied
    if EVAL_ID_RE.match(root.name):
        return root.parent.name
    return root.name


def scan_roots(model_root: Path, include_run_dirs: bool) -> list[Path]:
    roots = [model_root]
    if include_run_dirs and model_root.is_dir():
        roots.extend(sorted(p for p in model_root.iterdir() if p.is_dir() and (p / "status.json").exists()))
    return roots


def require_pandas(reason: str):
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(f"Reading {reason} requires pandas with the appropriate Excel engine installed") from exc
    return pd


def rows_from_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x if isinstance(x, dict) else {"value": x} for x in data]
    if isinstance(data, dict):
        if "columns" in data and "data" in data and isinstance(data["columns"], list):
            return [dict(zip(data["columns"], row)) for row in data.get("data", [])]
        values = list(data.values())
        if values and all(isinstance(v, list) for v in values):
            length = min(len(v) for v in values)
            return [{k: data[k][i] for k in data} for i in range(length)]
        return [data]
    return [{"value": data}]


def load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return rows_from_json(path)
    if suffix in {".csv", ".tsv"}:
        dialect = "excel-tab" if suffix == ".tsv" else "excel"
        with path.open(newline="", encoding="utf-8") as fh:
            return [dict(row) for row in csv.DictReader(fh, dialect=dialect)]
    if suffix == ".xlsx":
        pd = require_pandas(".xlsx files")
        frame = pd.read_excel(path)
        return frame.to_dict("records")
    raise ValueError(f"Unsupported file type: {path}")


def has_prediction_column(path: Path) -> bool:
    try:
        rows = load_rows(path)
    except Exception:
        return False
    return bool(rows) and any("prediction" in row for row in rows)


def explicit_prediction_candidates(root: Path, model_name: str, dataset: str, pred_format: str) -> list[Path]:
    suffixes = PRED_SUFFIXES if pred_format == "auto" else (f".{pred_format}",)
    return [root / f"{model_name}_{dataset}{suffix}" for suffix in suffixes]


def discover_predictions(root: Path, model_name: str) -> list[tuple[str, Path]]:
    if not root.is_dir():
        return []
    out: list[tuple[str, Path]] = []
    prefix = f"{model_name}_"
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.suffix.lower() not in PRED_SUFFIXES:
            continue
        stem = path.stem
        if not stem.startswith(prefix):
            continue
        if any(marker in stem for marker in TEMP_MARKERS):
            continue
        if not has_prediction_column(path):
            continue
        out.append((stem[len(prefix):], path))
    return out


def find_prediction(root: Path, model_name: str, dataset: str, pred_format: str) -> Path | None:
    for path in explicit_prediction_candidates(root, model_name, dataset, pred_format):
        if path.exists() and has_prediction_column(path):
            return path
    return None


def value_contains(value: Any, needle: str) -> bool:
    return needle in str(value)


def scan_prediction(path: Path, fail_substring: str) -> dict[str, Any]:
    rows = load_rows(path)
    total = len(rows)
    failed_indices = []
    for pos, row in enumerate(rows):
        pred = row.get("prediction", "")
        if value_contains(pred, fail_substring) or "Failed to obtain answer" in str(pred):
            failed_indices.append(str(row.get("index", pos)))
    return {"path": str(path), "total": total, "failed": len(failed_indices), "failed_indices": failed_indices[:20]}


def matching_eval_files(root: Path, model_name: str, dataset: str, prediction_path: Path | None) -> list[Path]:
    if not root.is_dir():
        return []
    prefix = f"{model_name}_{dataset}_"
    files = []
    for path in sorted(root.iterdir()):
        if not path.is_file() or path.suffix.lower() not in EVAL_SUFFIXES:
            continue
        if prediction_path is not None and path.resolve() == prediction_path.resolve():
            continue
        stem = path.stem
        if any(marker in stem for marker in TEMP_MARKERS):
            continue
        if stem.startswith(prefix):
            files.append(path)
    return files


def scan_eval_file(path: Path, fail_substring: str) -> dict[str, Any]:
    rows = load_rows(path)
    failed = 0
    total = len(rows)
    reasons: list[str] = []

    for row in rows:
        row_failed = False
        if "log" in row and (value_contains(row["log"], fail_substring) or "All 5 retries failed." in str(row["log"])):
            row_failed = True
        if "res" in row and value_contains(row["res"], fail_substring):
            row_failed = True
        if "gpt4_score" in row:
            try:
                if float(row["gpt4_score"]) == -1:
                    row_failed = True
            except Exception:
                pass
        if not row_failed:
            for key, value in row.items():
                if key in {"log", "res", "prediction"}:
                    continue
                if value_contains(value, fail_substring):
                    row_failed = True
                    break
        if row_failed:
            failed += 1

    if failed:
        reasons.append(f"{failed}/{total} rows matched failure markers")
    return {"path": str(path), "total": total, "failed": failed, "reasons": reasons}


def dataset_scan(root: Path, model_name: str, dataset: str, pred_format: str, fail_substring: str) -> dict[str, Any]:
    pred_path = find_prediction(root, model_name, dataset, pred_format)
    prediction = scan_prediction(pred_path, fail_substring) if pred_path is not None else None
    evals = [scan_eval_file(path, fail_substring) for path in matching_eval_files(root, model_name, dataset, pred_path)]
    return {"root": str(root), "model": model_name, "dataset": dataset, "prediction": prediction, "evaluations": evals}


def print_human(results: Iterable[dict[str, Any]], show_missing: bool) -> None:
    for item in results:
        model = item["model"]
        dataset = item["dataset"]
        prediction = item["prediction"]
        if prediction is None:
            if show_missing:
                print(f"MISSING prediction: model={model} dataset={dataset} root={item['root']}")
        else:
            failed = prediction["failed"]
            total = prediction["total"]
            if failed:
                pct = (failed / total * 100) if total else 0.0
                preview = ", ".join(prediction["failed_indices"][:10])
                print(
                    f"PREDICTION failures: model={model} dataset={dataset} "
                    f"failed={failed}/{total} ({pct:.2f}%) file={prediction['path']} indices={preview}"
                )
        for eval_item in item["evaluations"]:
            if eval_item["failed"]:
                print(
                    f"EVALUATION failures: model={model} dataset={dataset} "
                    f"failed={eval_item['failed']}/{eval_item['total']} file={eval_item['path']}"
                )


def main() -> int:
    args = parse_args()
    model_root = args.model_root
    model_name = infer_model_name(model_root, args.model_name)
    roots = scan_roots(model_root, args.include_run_dirs)

    results: list[dict[str, Any]] = []
    for root in roots:
        if args.datasets is None:
            for dataset, _ in discover_predictions(root, model_name):
                results.append(dataset_scan(root, model_name, dataset, args.pred_format, args.fail_substring))
        else:
            for dataset in args.datasets:
                results.append(dataset_scan(root, model_name, dataset, args.pred_format, args.fail_substring))

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_human(results, show_missing=args.show_missing)
        pred_failures = sum((item.get("prediction") or {}).get("failed", 0) for item in results)
        eval_failures = sum(e.get("failed", 0) for item in results for e in item.get("evaluations", []))
        missing = sum(1 for item in results if item.get("prediction") is None)
        print(f"Scanned datasets={len(results)} prediction_failures={pred_failures} evaluation_failures={eval_failures} missing_predictions={missing}")

    detected = False
    for item in results:
        if item.get("prediction") is None and args.show_missing:
            detected = True
        if (item.get("prediction") or {}).get("failed", 0):
            detected = True
        if any(e.get("failed", 0) for e in item.get("evaluations", [])):
            detected = True
    return 2 if args.fail_on_detected and detected else 0


if __name__ == "__main__":
    sys.exit(main())

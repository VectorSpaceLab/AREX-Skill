#!/usr/bin/env python3
"""Validate local AutoTrain vision/VLM folder layouts.

The helper checks the static rules enforced by AutoTrain preprocessors. It does
not import trainer code, upload data, or launch training.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except Exception as exc:  # pragma: no cover - environment triage
    print(f"ERROR: pandas is required for this helper: {exc!r}", file=sys.stderr)
    raise SystemExit(1)

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png"}


def image_files(path: Path) -> list[Path]:
    return [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES]


def parse_maybe(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception:
        return ast.literal_eval(value)


def normalize_task(task: str) -> str:
    raw = task.strip().lower().replace("_", "-")
    aliases = {
        "image-classification": "image-classification",
        "image-multi-class-classification": "image-classification",
        "image-binary-classification": "image-classification",
        "image-regression": "image-regression",
        "image-scoring": "image-regression",
        "image-single-column-regression": "image-regression",
        "object-detection": "object-detection",
        "image-object-detection": "object-detection",
    }
    if raw.startswith("vlm:"):
        return raw
    if raw == "vlm":
        return "vlm"
    if raw not in aliases:
        raise ValueError(f"unsupported vision task: {task}")
    return aliases[raw]


def validate_class_dir(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append(f"{label}: path does not exist: {path}")
        return {"path": str(path), "classes": {}}
    if not path.is_dir():
        errors.append(f"{label}: path is not a directory: {path}")
        return {"path": str(path), "classes": {}}

    class_dirs = sorted([p for p in path.iterdir() if p.is_dir()], key=lambda p: p.name)
    if len(class_dirs) < 2:
        errors.append(f"{label}: expected at least two class subfolders")

    summary: dict[str, int] = {}
    for class_dir in class_dirs:
        imgs = image_files(class_dir)
        summary[class_dir.name] = len(imgs)
        if len(imgs) < 5:
            errors.append(f"{label}.{class_dir.name}: expected at least five jpg/jpeg/png images")
        nested = [p.name for p in class_dir.iterdir() if p.is_dir()]
        if nested:
            errors.append(f"{label}.{class_dir.name}: nested subfolders are not allowed: {nested}")
        non_images = [p.name for p in class_dir.iterdir() if p.is_file() and p.suffix.lower() not in ALLOWED_SUFFIXES]
        if non_images:
            errors.append(f"{label}.{class_dir.name}: non-image files are not allowed: {non_images[:10]}")
    return {"path": str(path), "classes": summary}


def load_metadata(path: Path, label: str, errors: list[str]) -> pd.DataFrame | None:
    metadata_path = path / "metadata.jsonl"
    if not metadata_path.exists():
        errors.append(f"{label}: missing metadata.jsonl")
        return None
    try:
        return pd.read_json(metadata_path, lines=True)
    except Exception as exc:
        errors.append(f"{label}: failed to read metadata.jsonl: {exc}")
        return None


def validate_metadata_dir(path: Path, label: str, required: list[str], errors: list[str], warnings: list[str], parse_objects: bool = False) -> dict[str, Any]:
    if not path.exists() or not path.is_dir():
        errors.append(f"{label}: path is not an existing directory: {path}")
        return {"path": str(path), "rows": 0, "columns": []}

    imgs = image_files(path)
    if len(imgs) < 5:
        errors.append(f"{label}: expected at least five jpg/jpeg/png image files at the directory root")

    df = load_metadata(path, label, errors)
    if df is None:
        return {"path": str(path), "rows": 0, "columns": [], "image_count": len(imgs)}

    missing = [col for col in required if col not in df.columns]
    if missing:
        errors.append(f"{label}: missing metadata columns: {missing}")

    if "file_name" in df.columns:
        missing_refs = []
        for fname in df["file_name"].dropna().astype(str).tolist():
            ref = path / fname
            if not ref.exists():
                missing_refs.append(fname)
        if missing_refs:
            errors.append(f"{label}: metadata file_name values missing from directory: {missing_refs[:10]}")

    if "target" in required and "target" in df.columns:
        numeric = pd.to_numeric(df["target"], errors="coerce")
        if numeric.isna().any():
            warnings.append(f"{label}: some target values are not numeric")

    if parse_objects and "objects" in df.columns:
        for idx, value in df["objects"].dropna().head(5).items():
            try:
                parsed = parse_maybe(value)
            except Exception as exc:
                errors.append(f"{label}.objects row {idx}: cannot parse object annotation: {exc}")
                continue
            if not isinstance(parsed, (list, dict)):
                errors.append(f"{label}.objects row {idx}: expected list/dict annotation, got {type(parsed).__name__}")

    return {"path": str(path), "rows": int(len(df)), "columns": list(map(str, df.columns)), "image_count": len(imgs)}


def vlm_required_columns(args: argparse.Namespace, warnings: list[str]) -> list[str]:
    required = ["file_name"]
    mapping: dict[str, str] = {}
    if args.column_mapping_json:
        try:
            raw = json.loads(args.column_mapping_json)
        except Exception as exc:
            raise ValueError(f"--column-mapping-json is not valid JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError("--column-mapping-json must be a JSON object")
        mapping.update({str(k): str(v) for k, v in raw.items()})
    if args.text_column:
        mapping["text_column"] = args.text_column
    if args.prompt_text_column:
        mapping["prompt_text_column"] = args.prompt_text_column
    if not mapping:
        warnings.append("no VLM column mapping provided; checking only file_name")
    required.extend(sorted(set(mapping.values())))
    return required


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Training directory")
    parser.add_argument("--valid-path", type=Path, help="Optional validation directory")
    parser.add_argument("--task", required=True, help="Vision task alias, e.g. image-classification, object-detection, vlm:vqa")
    parser.add_argument("--text-column", help="VLM metadata text/caption/answer column")
    parser.add_argument("--prompt-text-column", help="VLM metadata prompt/question column")
    parser.add_argument("--column-mapping-json", help="Optional VLM column_mapping JSON object")
    args = parser.parse_args()

    warnings: list[str] = []
    errors: list[str] = []
    try:
        task = normalize_task(args.task)
        if task == "image-classification":
            summaries = [validate_class_dir(args.path, "train", errors)]
            if args.valid_path:
                summaries.append(validate_class_dir(args.valid_path, "validation", errors))
                train_classes = set(summaries[0].get("classes", {}).keys())
                valid_classes = set(summaries[1].get("classes", {}).keys())
                if train_classes and valid_classes and train_classes != valid_classes:
                    errors.append("validation: class subfolder names must match train")
        elif task == "image-regression":
            required = ["file_name", "target"]
            summaries = [validate_metadata_dir(args.path, "train", required, errors, warnings)]
            if args.valid_path:
                summaries.append(validate_metadata_dir(args.valid_path, "validation", required, errors, warnings))
        elif task == "object-detection":
            required = ["file_name", "objects"]
            summaries = [validate_metadata_dir(args.path, "train", required, errors, warnings, parse_objects=True)]
            if args.valid_path:
                summaries.append(validate_metadata_dir(args.valid_path, "validation", required, errors, warnings, parse_objects=True))
        elif task.startswith("vlm"):
            required = vlm_required_columns(args, warnings)
            summaries = [validate_metadata_dir(args.path, "train", required, errors, warnings)]
            if args.valid_path:
                summaries.append(validate_metadata_dir(args.valid_path, "validation", required, errors, warnings))
        else:
            raise ValueError(f"unsupported normalized task: {task}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    payload = {"task": task, "ok": not errors, "warnings": warnings, "errors": errors, "directories": summaries}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

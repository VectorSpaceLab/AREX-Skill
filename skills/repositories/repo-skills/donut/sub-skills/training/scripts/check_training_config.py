#!/usr/bin/env python3
"""Validate Donut training configs and local metadata.jsonl datasets.

Examples:
    python scripts/check_training_config.py --config references/configs/train_cord.yaml
    python scripts/check_training_config.py --dataset-root /path/to/dataset
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SPLIT_NAMES = ("train", "validation", "test")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check a Donut training config and any local metadata.jsonl rows it references.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config", help="Path to a Donut YAML config file.")
    parser.add_argument("--dataset-root", help="Optional local dataset root to validate directly.")
    return parser


def load_yaml_config(path: Path) -> Dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read Donut YAML configs") from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: config root must be a mapping")
    return data


def as_list(value: Any, field_name: str, errors: List[str]) -> List[Any]:
    if isinstance(value, tuple):
        value = list(value)
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list, got {type(value).__name__}")
        return []
    return value


def ensure_positive_int(value: Any, field_name: str, errors: List[str], allow_zero: bool = False) -> None:
    if isinstance(value, str):
        try:
            value = int(value)
        except ValueError:
            errors.append(f"{field_name} must be an integer, got {type(value).__name__}")
            return
    if not isinstance(value, int):
        errors.append(f"{field_name} must be an integer, got {type(value).__name__}")
        return
    if allow_zero:
        if value < 0:
            errors.append(f"{field_name} must be >= 0, got {value}")
    elif value <= 0:
        errors.append(f"{field_name} must be > 0, got {value}")


def validate_metadata_file(metadata_path: Path, errors: List[str], warnings: List[str]) -> None:
    split_root = metadata_path.parent
    with metadata_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{metadata_path}:{line_no}: invalid JSON: {exc.msg}")
                continue

            if not isinstance(record, dict):
                errors.append(f"{metadata_path}:{line_no}: each row must be a JSON object")
                continue

            file_name = record.get("file_name")
            if not isinstance(file_name, str) or not file_name:
                errors.append(f"{metadata_path}:{line_no}: file_name must be a non-empty string")
            else:
                image_path = Path(file_name)
                if not image_path.is_absolute():
                    image_path = split_root / image_path
                if not image_path.exists():
                    errors.append(f"{metadata_path}:{line_no}: image file not found at {image_path}")

            if "ground_truth" not in record:
                errors.append(f"{metadata_path}:{line_no}: missing ground_truth")
                continue

            ground_truth_raw = record["ground_truth"]
            if not isinstance(ground_truth_raw, str):
                errors.append(f"{metadata_path}:{line_no}: ground_truth must be a JSON-encoded string")
                continue

            try:
                ground_truth = json.loads(ground_truth_raw)
            except json.JSONDecodeError as exc:
                errors.append(f"{metadata_path}:{line_no}: ground_truth is not valid JSON: {exc.msg}")
                continue

            if not isinstance(ground_truth, dict):
                errors.append(f"{metadata_path}:{line_no}: ground_truth must decode to a JSON object")
                continue

            if "gt_parse" in ground_truth:
                if not isinstance(ground_truth["gt_parse"], dict):
                    errors.append(f"{metadata_path}:{line_no}: gt_parse must be a dictionary")
            elif "gt_parses" in ground_truth:
                if not isinstance(ground_truth["gt_parses"], list):
                    errors.append(f"{metadata_path}:{line_no}: gt_parses must be a list")
                elif not ground_truth["gt_parses"]:
                    errors.append(f"{metadata_path}:{line_no}: gt_parses must not be empty")
                else:
                    for qa_index, qa in enumerate(ground_truth["gt_parses"]):
                        if not isinstance(qa, dict):
                            errors.append(f"{metadata_path}:{line_no}: gt_parses[{qa_index}] must be a dict")
            else:
                errors.append(f"{metadata_path}:{line_no}: missing gt_parse or gt_parses")


def validate_local_dataset_root(dataset_root: Path, errors: List[str], warnings: List[str]) -> None:
    if (dataset_root / "metadata.jsonl").is_file():
        validate_metadata_file(dataset_root / "metadata.jsonl", errors, warnings)
        return

    found = False
    for split_name in SPLIT_NAMES:
        metadata_path = dataset_root / split_name / "metadata.jsonl"
        if metadata_path.is_file():
            found = True
            validate_metadata_file(metadata_path, errors, warnings)
    if not found:
        warnings.append(f"{dataset_root}: no metadata.jsonl files were found under train/, validation/, or test/")


def validate_config(config: Dict[str, Any], errors: List[str], warnings: List[str], infos: List[str]) -> None:
    dataset_name_or_paths = as_list(config.get("dataset_name_or_paths"), "dataset_name_or_paths", errors)
    train_batch_sizes = as_list(config.get("train_batch_sizes"), "train_batch_sizes", errors)
    val_batch_sizes = as_list(config.get("val_batch_sizes"), "val_batch_sizes", errors)
    task_start_tokens = config.get("task_start_tokens")
    if task_start_tokens is not None:
        task_start_tokens = as_list(task_start_tokens, "task_start_tokens", errors)

    input_size = config.get("input_size")
    if isinstance(input_size, (list, tuple)) and len(input_size) == 2:
        for index, item in enumerate(input_size):
            if not isinstance(item, int) or item <= 0:
                errors.append(f"input_size[{index}] must be a positive integer")
    else:
        errors.append("input_size must be a list of two positive integers")

    for field_name in (
        "max_length",
        "num_nodes",
        "seed",
        "warmup_steps",
        "num_training_samples_per_epoch",
        "num_workers",
        "check_val_every_n_epoch",
    ):
        if field_name in config:
            ensure_positive_int(config[field_name], field_name, errors)

    for field_name in ("max_epochs", "max_steps"):
        if field_name in config:
            value = config[field_name]
            if not isinstance(value, int):
                errors.append(f"{field_name} must be an integer, got {type(value).__name__}")
            elif value != -1 and value <= 0:
                errors.append(f"{field_name} must be -1 or a positive integer, got {value}")

    for field_name in ("lr", "val_check_interval", "gradient_clip_val"):
        if field_name not in config:
            continue
        value = config[field_name]
        if isinstance(value, str):
            try:
                float(value)
            except ValueError:
                errors.append(f"{field_name} must be numeric, got {type(value).__name__}")
        elif not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be numeric, got {type(value).__name__}")

    if not dataset_name_or_paths:
        errors.append("dataset_name_or_paths must not be empty")
    if dataset_name_or_paths and train_batch_sizes and len(dataset_name_or_paths) != len(train_batch_sizes):
        errors.append("dataset_name_or_paths and train_batch_sizes must have the same length")
    if dataset_name_or_paths and val_batch_sizes and len(dataset_name_or_paths) != len(val_batch_sizes):
        errors.append("dataset_name_or_paths and val_batch_sizes must have the same length")
    if task_start_tokens is not None and dataset_name_or_paths and len(task_start_tokens) != len(dataset_name_or_paths):
        errors.append("task_start_tokens must match the dataset list length")

    max_epochs = config.get("max_epochs", -1)
    max_steps = config.get("max_steps", -1)
    if isinstance(max_epochs, int) and max_epochs > 0 and len(dataset_name_or_paths) > 1:
        errors.append("Set max_epochs only if the number of datasets is 1")
    if isinstance(max_epochs, int) and max_epochs <= 0 and isinstance(max_steps, int) and max_steps <= 0:
        errors.append("At least one of max_epochs or max_steps must be > 0")

    if "pretrained_model_name_or_path" not in config:
        warnings.append("pretrained_model_name_or_path is missing; training from scratch is allowed, but most examples start from a pretrained backbone")

    if "result_path" not in config:
        warnings.append("result_path is missing; the source examples default to ./result")

    for index, dataset_entry in enumerate(dataset_name_or_paths):
        if not isinstance(dataset_entry, str) or not dataset_entry:
            errors.append(f"dataset_name_or_paths[{index}] must be a non-empty string")
            continue
        dataset_path = Path(dataset_entry).expanduser()
        path_like = dataset_entry.startswith((".", "/", "~"))
        if dataset_path.exists():
            infos.append(f"dataset_name_or_paths[{index}] points to a local dataset root; validating metadata.jsonl files")
            validate_local_dataset_root(dataset_path, errors, warnings)
            task_name = dataset_path.name
            if task_name == "docvqa":
                infos.append(f"dataset_name_or_paths[{index}] looks like DocVQA; the source trainer uses <s_answer> as the prompt end token")
            elif task_name == "rvlcdip":
                infos.append(f"dataset_name_or_paths[{index}] looks like RVL-CDIP; the trainer adds class special tokens automatically")
        elif path_like:
            warnings.append(f"dataset_name_or_paths[{index}] looks like a local path but does not exist yet: {dataset_entry}")
        else:
            infos.append(f"dataset_name_or_paths[{index}] does not exist locally; treating it as a Hugging Face dataset id")

    resume_path = config.get("resume_from_checkpoint_path")
    if isinstance(resume_path, str) and resume_path:
        resume_root = Path(resume_path)
        if resume_root.exists() and not (resume_root / "artifacts.ckpt").is_file() and not resume_root.name.endswith(".ckpt"):
            warnings.append(
                "resume_from_checkpoint_path exists but does not obviously contain artifacts.ckpt; verify the run directory prefix"
            )


def print_report(title: str, items: List[str]) -> None:
    if not items:
        return
    print(f"{title}:")
    for item in items:
        print(f"  - {item}")


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: List[str] = []
    warnings: List[str] = []
    infos: List[str] = []

    if not args.config and not args.dataset_root:
        print("error: provide --config, --dataset-root, or both", file=sys.stderr)
        return 2

    config: Dict[str, Any] = {}
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_file():
            print(f"error: config file not found: {config_path}", file=sys.stderr)
            return 2
        config = load_yaml_config(config_path)
        validate_config(config, errors, warnings, infos)

    if args.dataset_root:
        dataset_root = Path(args.dataset_root)
        if not dataset_root.exists():
            errors.append(f"dataset_root does not exist: {dataset_root}")
        else:
            validate_local_dataset_root(dataset_root, errors, warnings)

    print_report("Info", infos)
    print_report("Warnings", warnings)
    print_report("Errors", errors)

    if errors:
        print("Training config validation failed.")
        return 1

    print("Training config validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
